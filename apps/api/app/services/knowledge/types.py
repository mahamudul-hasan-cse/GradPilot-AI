"""Shared types for the AI Knowledge Platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


SOURCE_TYPES = frozenset({
    "university",
    "scholarship",
    "profile_analysis",
    "recommendation_history",
    "country_guide",
    "visa_requirement",
    "admission_requirement",
    "sop_knowledge",
})


@dataclass
class KnowledgeChunk:
    document_id: UUID
    source_type: str
    source_id: str | None
    title: str
    content: str
    score: float = 0.0
    rank: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def citation_key(self) -> str:
        return f"[{self.source_type}:{self.document_id}]"


@dataclass
class RetrievalResult:
    chunks: list[KnowledgeChunk]
    query: str
    rewritten_query: str
    retrieval_method: str = "hybrid_rrf"


@dataclass
class Citation:
    index: int
    document_id: UUID
    source_type: str
    title: str
    excerpt: str
    source_id: str | None = None


@dataclass
class KnowledgeAnswer:
    answer: str
    citations: list[Citation]
    sources: list[KnowledgeChunk]
    confidence: float
    validation_passed: bool
    hallucination_risk: str
    rewritten_query: str
    model: str


@dataclass
class ChatMessage:
    role: str
    content: str
    citations: list[dict[str, Any]] | None = None
