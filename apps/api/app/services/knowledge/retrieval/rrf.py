"""Reciprocal Rank Fusion for hybrid retrieval."""

from __future__ import annotations

from uuid import UUID

from app.services.knowledge.types import KnowledgeChunk


def reciprocal_rank_fusion(
    ranked_lists: list[list[KnowledgeChunk]],
    *,
    k: int = 60,
    top_n: int = 12,
) -> list[KnowledgeChunk]:
    """Merge multiple ranked lists using RRF (Cormack et al.)."""
    scores: dict[UUID, float] = {}
    chunks: dict[UUID, KnowledgeChunk] = {}

    for ranked in ranked_lists:
        for rank, chunk in enumerate(ranked, start=1):
            scores[chunk.document_id] = scores.get(chunk.document_id, 0.0) + 1.0 / (k + rank)
            chunks[chunk.document_id] = chunk

    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    result: list[KnowledgeChunk] = []
    for doc_id, score in fused:
        chunk = chunks[doc_id]
        chunk.score = score
        result.append(chunk)
    return result
