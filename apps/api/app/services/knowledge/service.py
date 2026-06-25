"""Knowledge Service — RAG orchestration for the AI Knowledge Platform."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_session import ChatSession
from app.models.profile_analysis import ProfileAnalysis
from app.models.recommendation import RecommendationHistory
from app.repositories.chat_session import ChatSessionRepository
from app.services.knowledge.indexer import KnowledgeIndexer
from app.services.knowledge.llm.providers import get_llm_provider
from app.services.knowledge.memory.conversation_memory import ConversationMemory
from app.services.knowledge.pipeline.answer_validator import AnswerValidator
from app.services.knowledge.pipeline.citation_generator import CitationGenerator
from app.services.knowledge.pipeline.context_builder import ContextBuilder, ContextCompressor
from app.services.knowledge.pipeline.hallucination_guard import HallucinationGuard
from app.services.knowledge.pipeline.query_rewriter import QueryRewriter
from app.services.knowledge.prompts.prompt_manager import PromptManager
from app.services.knowledge.retrieval.hybrid import HybridRetriever
from app.services.knowledge.types import ChatMessage, Citation, KnowledgeAnswer, KnowledgeChunk, RetrievalResult

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retriever = HybridRetriever(db)
        self.query_rewriter = QueryRewriter()
        self.context_builder = ContextBuilder()
        self.context_compressor = ContextCompressor()
        self.prompt_manager = PromptManager()
        self.citation_generator = CitationGenerator()
        self.hallucination_guard = HallucinationGuard()
        self.answer_validator = AnswerValidator()
        self.memory = ConversationMemory()
        self.chat_repo = ChatSessionRepository(db)

    async def search(
        self,
        query: str,
        *,
        source_types: list[str] | None = None,
        limit: int = 10,
        user_id: UUID | None = None,
    ) -> RetrievalResult:
        history = ""
        rewritten = self.query_rewriter.rewrite(query, conversation_context=history)
        result = await self.retriever.retrieve(rewritten, source_types=source_types, limit=limit)
        result.rewritten_query = rewritten
        if user_id:
            personal = await self._personal_chunks(user_id)
            result.chunks = personal + result.chunks
            result.chunks = result.chunks[:limit]
        return result

    async def answer(
        self,
        question: str,
        *,
        session_id: UUID | None = None,
        user_id: UUID | None = None,
        source_types: list[str] | None = None,
        llm_provider: str | None = None,
        stream: bool = False,
    ) -> KnowledgeAnswer | AsyncIterator[str]:
        session, messages = await self._load_session(session_id, user_id)
        history = self.memory.format_history(messages)
        rewritten = self.query_rewriter.rewrite(question, conversation_context=history)

        retrieval = await self.retriever.retrieve(rewritten, source_types=source_types, limit=12)
        if user_id:
            personal = await self._personal_chunks(user_id)
            retrieval.chunks = personal + retrieval.chunks

        compressed = self.context_compressor.compress(retrieval.chunks)
        context = self.context_builder.build(compressed)
        user_prompt = self.prompt_manager.build_user_prompt(
            context=context, question=question, history=history or None
        )
        llm = get_llm_provider(llm_provider)

        if stream:
            return self._stream_answer(
                llm=llm,
                session=session,
                messages=messages,
                question=question,
                retrieval=retrieval,
                compressed=compressed,
                context=context,
                user_prompt=user_prompt,
            )

        raw_answer = await llm.generate(
            system=self.prompt_manager.SYSTEM_PROMPT,
            user=user_prompt,
        )
        return await self._finalize_answer(
            raw_answer=raw_answer,
            question=question,
            retrieval=retrieval,
            compressed=compressed,
            rewritten=rewritten,
            llm_name=llm.provider_name,
            session=session,
            messages=messages,
        )

    async def _finalize_answer(
        self,
        *,
        raw_answer: str,
        question: str,
        retrieval: RetrievalResult,
        compressed: list[KnowledgeChunk],
        rewritten: str,
        llm_name: str,
        session: ChatSession | None,
        messages: list[ChatMessage],
    ) -> KnowledgeAnswer:
        citations = self.citation_generator.generate(raw_answer, compressed)
        answer = self.citation_generator.inject_inline_citations(raw_answer, citations)
        risk, confidence = self.hallucination_guard.assess(answer, compressed)
        passed, issues = self.answer_validator.validate(
            answer,
            question=question,
            chunks=compressed,
            citations=citations,
            confidence=confidence,
            hallucination_risk=risk,
        )
        if not passed and risk == "high":
            answer = (
                f"{answer}\n\n_Note: This response may contain unverified details. "
                f"Please verify against official sources. Issues: {', '.join(issues)}_"
            )

        if session:
            await self._persist_turn(session, messages, question, answer, citations)

        return KnowledgeAnswer(
            answer=answer,
            citations=citations,
            sources=compressed,
            confidence=confidence,
            validation_passed=passed,
            hallucination_risk=risk,
            rewritten_query=rewritten,
            model=llm_name,
        )

    async def _stream_answer(
        self,
        *,
        llm,
        session: ChatSession | None,
        messages: list[ChatMessage],
        question: str,
        retrieval: RetrievalResult,
        compressed: list[KnowledgeChunk],
        context: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        full_parts: list[str] = []

        meta = {
            "type": "metadata",
            "sources": [
                {
                    "index": i + 1,
                    "title": c.title,
                    "source_type": c.source_type,
                    "document_id": str(c.document_id),
                }
                for i, c in enumerate(compressed)
            ],
            "rewritten_query": retrieval.rewritten_query,
        }
        yield f"data: {json.dumps(meta)}\n\n"

        async for token in llm.stream(system=self.prompt_manager.SYSTEM_PROMPT, user=user_prompt):
            full_parts.append(token)
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        raw_answer = "".join(full_parts)
        citations = self.citation_generator.generate(raw_answer, compressed)
        risk, confidence = self.hallucination_guard.assess(raw_answer, compressed)
        done = {
            "type": "done",
            "citations": [
                {
                    "index": c.index,
                    "title": c.title,
                    "source_type": c.source_type,
                    "excerpt": c.excerpt,
                    "document_id": str(c.document_id),
                }
                for c in citations
            ],
            "confidence": confidence,
            "hallucination_risk": risk,
        }
        yield f"data: {json.dumps(done)}\n\n"

        if session:
            answer = self.citation_generator.inject_inline_citations(raw_answer, citations)
            await self._persist_turn(session, messages, question, answer, citations)

    async def _load_session(
        self,
        session_id: UUID | None,
        user_id: UUID | None,
    ) -> tuple[ChatSession | None, list[ChatMessage]]:
        if not session_id or not user_id:
            return None, []
        session = await self.chat_repo.get_for_user(session_id, user_id)
        if not session:
            return None, []
        cached = await self.memory.get_messages(session_id)
        if cached:
            return session, cached
        db_messages = [
            ChatMessage(role=m.get("role", "user"), content=m.get("content", ""), citations=m.get("citations"))
            for m in (session.messages or [])
        ]
        return session, db_messages

    async def _persist_turn(
        self,
        session: ChatSession,
        messages: list[ChatMessage],
        question: str,
        answer: str,
        citations: list[Citation],
    ) -> None:
        citation_dicts = [
            {"index": c.index, "title": c.title, "source_type": c.source_type, "excerpt": c.excerpt}
            for c in citations
        ]
        messages.append(ChatMessage(role="user", content=question))
        messages.append(ChatMessage(role="assistant", content=answer, citations=citation_dicts))
        session.messages = ConversationMemory.to_db_messages(messages)
        if not session.title and question:
            session.title = question[:80]
        await self.db.flush()
        await self.memory.set_messages(session.id, messages)

    async def create_session(self, user_id: UUID, *, title: str | None = None) -> ChatSession:
        session = ChatSession(
            id=uuid4(),
            user_id=user_id,
            title=title,
            session_type="knowledge",
            messages=[],
            is_active=True,
        )
        return await self.chat_repo.create(session)

    async def list_conversations(self, user_id: UUID) -> list[ChatSession]:
        return await self.chat_repo.get_by_user(user_id)

    async def index_knowledge_base(self) -> dict[str, int]:
        indexer = KnowledgeIndexer(self.db)
        return await indexer.index_all()

    async def _personal_chunks(self, user_id: UUID) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []

        profile_result = await self.db.execute(
            select(ProfileAnalysis)
            .where(ProfileAnalysis.user_id == user_id)
            .order_by(ProfileAnalysis.created_at.desc())
            .limit(1)
        )
        profile = profile_result.scalar_one_or_none()
        if profile:
            summary = profile.response_summary or {}
            content = (
                f"Latest profile analysis: admission readiness {profile.admission_readiness_score}, "
                f"scholarship readiness {profile.scholarship_readiness_score}, "
                f"employability {profile.employability_score}, "
                f"tier {profile.recommended_university_tier}. "
                f"Summary: {json.dumps(summary)}"
            )
            chunks.append(
                KnowledgeChunk(
                    document_id=profile.id,
                    source_type="profile_analysis",
                    source_id=str(profile.id),
                    title="Your Profile Analysis",
                    content=content,
                    score=1.0,
                    metadata={"user_id": str(user_id)},
                )
            )

        rec_result = await self.db.execute(
            select(RecommendationHistory)
            .where(RecommendationHistory.user_id == user_id)
            .order_by(RecommendationHistory.created_at.desc())
            .limit(3)
        )
        for rec in rec_result.scalars().all():
            chunks.append(
                KnowledgeChunk(
                    document_id=rec.id,
                    source_type="recommendation_history",
                    source_id=str(rec.id),
                    title="University Recommendation History",
                    content=json.dumps(rec.response_summary or {}, default=str),
                    score=0.9,
                    metadata={"user_id": str(user_id)},
                )
            )
        return chunks
