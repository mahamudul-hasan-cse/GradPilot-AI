"""Tests for the AI Knowledge Platform."""

from uuid import uuid4

import pytest

from app.services.knowledge.pipeline.answer_validator import AnswerValidator
from app.services.knowledge.pipeline.citation_generator import CitationGenerator
from app.services.knowledge.pipeline.context_builder import ContextBuilder, ContextCompressor
from app.services.knowledge.pipeline.hallucination_guard import HallucinationGuard
from app.services.knowledge.pipeline.query_rewriter import QueryRewriter
from app.services.knowledge.prompts.prompt_manager import PromptManager
from app.services.knowledge.retrieval.bm25 import BM25Scorer, tokenize
from app.services.knowledge.retrieval.rrf import reciprocal_rank_fusion
from app.services.knowledge.types import KnowledgeChunk


def _chunk(title: str, content: str, score: float = 0.5) -> KnowledgeChunk:
    return KnowledgeChunk(
        document_id=uuid4(),
        source_type="country_guide",
        source_id="test",
        title=title,
        content=content,
        score=score,
    )


class TestTokenize:
    def test_basic(self):
        assert "ielts" in tokenize("IELTS score requirements")


class TestBM25:
    def test_ranks_relevant_higher(self):
        scorer = BM25Scorer()
        chunks = [
            _chunk("USA Guide", "F-1 visa requirements for international students"),
            _chunk("UK Guide", "Football and cricket in London"),
        ]
        ranked = scorer.score("F-1 visa USA", chunks)
        assert ranked[0][0].title == "USA Guide"
        assert ranked[0][1] > ranked[1][1]


class TestRRF:
    def test_merges_lists(self):
        a = _chunk("A", "content a")
        b = _chunk("B", "content b")
        c = _chunk("C", "content c")
        b2 = KnowledgeChunk(
            document_id=b.document_id,
            source_type=b.source_type,
            source_id=b.source_id,
            title=b.title,
            content=b.content,
        )
        fused = reciprocal_rank_fusion([[a, b], [b2, c]], top_n=3)
        ids = [x.document_id for x in fused]
        assert b.document_id in ids
        assert len(fused) == 3


class TestQueryRewriter:
    def test_expands_ielts(self):
        rewriter = QueryRewriter()
        result = rewriter.rewrite("What IELTS score do I need?")
        assert "IELTS" in result
        assert "English" in result

    def test_includes_context(self):
        rewriter = QueryRewriter()
        result = rewriter.rewrite("Tell me more", conversation_context="User asked about UK visas")
        assert "UK visas" in result


class TestContextBuilder:
    def test_builds_numbered_sources(self):
        builder = ContextBuilder()
        text = builder.build([_chunk("USA F-1", "SEVIS fee and DS-160 form")])
        assert "[Source 1]" in text
        assert "SEVIS" in text

    def test_empty_context(self):
        builder = ContextBuilder()
        assert "No relevant context" in builder.build([])


class TestContextCompressor:
    def test_compresses_chunks(self):
        compressor = ContextCompressor()
        chunks = [_chunk("Long", "Sentence one. " * 50, score=0.9)]
        result = compressor.compress(chunks, max_chars=200)
        assert len(result[0].content) <= 250


class TestCitationGenerator:
    def test_extracts_source_refs(self):
        gen = CitationGenerator()
        chunks = [_chunk("USA Guide", "F-1 visa steps")]
        citations = gen.generate("According to [Source 1], you need an I-20.", chunks)
        assert len(citations) == 1
        assert citations[0].index == 1

    def test_fallback_citations(self):
        gen = CitationGenerator()
        chunks = [_chunk("Guide", "Content")]
        citations = gen.generate("Answer without explicit refs.", chunks)
        assert len(citations) >= 1


class TestHallucinationGuard:
    def test_low_risk_when_grounded(self):
        guard = HallucinationGuard()
        chunks = [_chunk("MIT", "Massachusetts Institute of Technology admissions")]
        risk, confidence = guard.assess(
            "Massachusetts Institute of Technology has competitive admissions.",
            chunks,
        )
        assert risk in {"low", "medium"}
        assert confidence > 0.3

    def test_high_risk_without_context(self):
        guard = HallucinationGuard()
        risk, _ = guard.assess("Harvard University deadline is tomorrow.", [])
        assert risk == "high"


class TestAnswerValidator:
    def test_valid_answer(self):
        validator = AnswerValidator()
        chunks = [_chunk("Guide", "Content")]
        from app.services.knowledge.types import Citation

        citations = [
            Citation(index=1, document_id=chunks[0].document_id, source_type="guide", title="Guide", excerpt="x")
        ]
        passed, issues = validator.validate(
            "A sufficiently long grounded answer with details.",
            question="Q?",
            chunks=chunks,
            citations=citations,
            confidence=0.8,
            hallucination_risk="low",
        )
        assert passed or len(issues) <= 1


class TestPromptManager:
    def test_builds_user_prompt(self):
        pm = PromptManager()
        prompt = pm.build_user_prompt(context="Some context", question="What visa do I need?")
        assert "Context:" in prompt
        assert "What visa do I need?" in prompt
        assert "[Source N]" in prompt or "citations" in prompt.lower()

    def test_system_prompt_is_grounded(self):
        assert "NOT a generic chatbot" in PromptManager.SYSTEM_PROMPT or "knowledge" in PromptManager.SYSTEM_PROMPT.lower()
