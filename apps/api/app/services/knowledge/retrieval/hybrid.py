"""Hybrid retriever — PostgreSQL + Qdrant + BM25 + RRF."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.knowledge_document import KnowledgeDocumentRepository
from app.services.knowledge.retrieval.bm25 import BM25Scorer
from app.services.knowledge.retrieval.rrf import reciprocal_rank_fusion
from app.services.knowledge.retrieval.semantic import KnowledgeVectorStore
from app.services.knowledge.types import KnowledgeChunk, RetrievalResult


class HybridRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = KnowledgeDocumentRepository(db)
        self.vector_store = KnowledgeVectorStore()
        self.bm25 = BM25Scorer()

    async def retrieve(
        self,
        query: str,
        *,
        source_types: list[str] | None = None,
        limit: int = 12,
    ) -> RetrievalResult:
        pg_ranked = await self._postgres_search(query, source_types=source_types)
        semantic_ranked = self.vector_store.semantic_search(
            query, source_types=source_types, limit=limit * 2
        )
        await self._hydrate_semantic_chunks(semantic_ranked)

        union_map: dict[UUID, KnowledgeChunk] = {c.document_id: c for c in pg_ranked}
        for c in semantic_ranked:
            union_map.setdefault(c.document_id, c)
        bm25_input = list(union_map.values())
        bm25_ranked = [c for c, _ in self.bm25.score(query, bm25_input)]

        fused = reciprocal_rank_fusion(
            [pg_ranked, semantic_ranked, bm25_ranked],
            top_n=limit,
        )
        return RetrievalResult(chunks=fused, query=query, rewritten_query=query)

    async def _postgres_search(
        self,
        query: str,
        *,
        source_types: list[str] | None,
    ) -> list[KnowledgeChunk]:
        ranked = await self.doc_repo.keyword_search(query, source_types=source_types, limit=30)
        if ranked:
            return [
                KnowledgeChunk(
                    document_id=doc.id,
                    source_type=doc.source_type,
                    source_id=doc.source_id,
                    title=doc.title,
                    content=doc.content,
                    score=score,
                    metadata=doc.doc_metadata or {},
                )
                for doc, score in ranked
            ]
        fallback = await self.doc_repo.fallback_ilike_search(query, source_types=source_types, limit=20)
        return [
            KnowledgeChunk(
                document_id=doc.id,
                source_type=doc.source_type,
                source_id=doc.source_id,
                title=doc.title,
                content=doc.content,
                score=0.5,
                metadata=doc.doc_metadata or {},
            )
            for doc in fallback
        ]

    async def _hydrate_semantic_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        missing = [c for c in chunks if not c.content]
        if not missing:
            return
        docs = await self.doc_repo.get_by_ids([c.document_id for c in missing])
        by_id = {d.id: d for d in docs}
        for chunk in missing:
            doc = by_id.get(chunk.document_id)
            if doc:
                chunk.title = doc.title
                chunk.content = doc.content
                chunk.source_type = doc.source_type
                chunk.source_id = doc.source_id
                chunk.metadata = doc.doc_metadata or {}
