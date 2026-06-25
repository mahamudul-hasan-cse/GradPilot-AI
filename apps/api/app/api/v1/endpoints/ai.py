"""AI Knowledge Platform endpoints — RAG, search, and conversations."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_current_active_user_optional
from app.db.session import get_db
from app.models.user import User
from app.schemas.knowledge import (
    CitationResponse,
    ConversationListResponse,
    ConversationSummary,
    KnowledgeChatRequest,
    KnowledgeChatResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResultItem,
)
from app.services.knowledge.service import KnowledgeService

router = APIRouter(prefix="/ai", tags=["AI Knowledge Platform"])


@router.post("/search", response_model=KnowledgeSearchResponse)
async def knowledge_search(
    request: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_active_user_optional),
) -> KnowledgeSearchResponse:
    """
    Hybrid knowledge search across GradPilot's verified sources.

    Combines **PostgreSQL full-text**, **Qdrant semantic search**, and **BM25**
    with **Reciprocal Rank Fusion** for ranked results.

    Sources: universities, scholarships, country guides, visa requirements,
    admission requirements, SOP knowledge, and (when authenticated) profile analysis.
    """
    service = KnowledgeService(db)
    user_id = current_user.id if current_user else None
    result = await service.search(
        request.query,
        source_types=request.source_types,
        limit=request.limit,
        user_id=user_id,
    )
    return KnowledgeSearchResponse(
        query=request.query,
        rewritten_query=result.rewritten_query,
        results=[
            KnowledgeSearchResultItem(
                document_id=c.document_id,
                source_type=c.source_type,
                source_id=c.source_id,
                title=c.title,
                content=c.content[:500],
                score=c.score,
                metadata=c.metadata,
            )
            for c in result.chunks
        ],
        total=len(result.chunks),
    )


@router.post("/chat")
async def knowledge_chat(
    request: KnowledgeChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Knowledge-grounded Q&A with citations — **not a generic chatbot**.

    Pipeline: Query Rewriter → Hybrid Retriever → Context Builder → LLM →
    Citation Generator → Hallucination Guard → Answer Validator.

    Supports **streaming** (SSE) when `stream=true`.
    Multi-turn memory via Redis + PostgreSQL session persistence.
  """
    service = KnowledgeService(db)
    session_id = request.session_id
    if session_id is None:
        session = await service.create_session(current_user.id)
        session_id = session.id

    if request.stream:
        stream_iter = await service.answer(
            request.message,
            session_id=session_id,
            user_id=current_user.id,
            source_types=request.source_types,
            llm_provider=request.llm_provider,
            stream=True,
        )

        async def event_stream():
            async for chunk in stream_iter:
                yield chunk

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    answer = await service.answer(
        request.message,
        session_id=session_id,
        user_id=current_user.id,
        source_types=request.source_types,
        llm_provider=request.llm_provider,
        stream=False,
    )
    if not isinstance(answer, object) or not hasattr(answer, "answer"):
        raise HTTPException(status_code=500, detail="Unexpected response from knowledge service")

    return KnowledgeChatResponse(
        answer=answer.answer,
        citations=[
            CitationResponse(
                index=c.index,
                document_id=c.document_id,
                source_type=c.source_type,
                title=c.title,
                excerpt=c.excerpt,
                source_id=c.source_id,
            )
            for c in answer.citations
        ],
        confidence=answer.confidence,
        validation_passed=answer.validation_passed,
        hallucination_risk=answer.hallucination_risk,
        rewritten_query=answer.rewritten_query,
        model=answer.model,
        session_id=session_id,
        sources=[
            KnowledgeSearchResultItem(
                document_id=s.document_id,
                source_type=s.source_type,
                source_id=s.source_id,
                title=s.title,
                content=s.content[:400],
                score=s.score,
                metadata=s.metadata,
            )
            for s in answer.sources
        ],
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ConversationListResponse:
    """List the authenticated user's knowledge conversation sessions."""
    service = KnowledgeService(db)
    sessions = await service.list_conversations(current_user.id)
    return ConversationListResponse(
        conversations=[
            ConversationSummary(
                id=s.id,
                title=s.title,
                session_type=s.session_type,
                message_count=len(s.messages or []),
                created_at=s.created_at.isoformat(),
                updated_at=s.updated_at.isoformat(),
            )
            for s in sessions
        ],
        total=len(sessions),
    )


@router.post("/index", status_code=status.HTTP_202_ACCEPTED)
async def index_knowledge_base(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Re-index knowledge base from universities, scholarships, and static guides.
    Indexes into PostgreSQL + Qdrant.
    """
    service = KnowledgeService(db)
    counts = await service.index_knowledge_base()
    return {"status": "indexed", "counts": counts, "triggered_by": str(current_user.id)}
