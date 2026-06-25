"""Qdrant semantic search for knowledge documents."""

from __future__ import annotations

import logging
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import settings
from app.services.embedding import VECTOR_SIZE, get_embedding_provider
from app.services.knowledge.types import KnowledgeChunk

logger = logging.getLogger(__name__)

KNOWLEDGE_COLLECTION = "knowledge"


class KnowledgeVectorStore:
    def __init__(self) -> None:
        self._client: QdrantClient | None = None
        self._embedder = get_embedding_provider()

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        return self._client

    def ensure_collection(self) -> None:
        client = self._get_client()
        collections = {c.name for c in client.get_collections().collections}
        if KNOWLEDGE_COLLECTION not in collections:
            client.create_collection(
                collection_name=KNOWLEDGE_COLLECTION,
                vectors_config=qmodels.VectorParams(size=VECTOR_SIZE, distance=qmodels.Distance.COSINE),
            )

    def upsert(self, *, document_id: UUID, text: str, payload: dict) -> None:
        self.ensure_collection()
        vector = self._embedder.embed(text)
        self._get_client().upsert(
            collection_name=KNOWLEDGE_COLLECTION,
            points=[
                qmodels.PointStruct(
                    id=str(document_id),
                    vector=vector,
                    payload={**payload, "document_id": str(document_id)},
                )
            ],
        )

    def delete(self, document_id: UUID) -> None:
        try:
            self._get_client().delete(
                collection_name=KNOWLEDGE_COLLECTION,
                points_selector=qmodels.PointIdsList(points=[str(document_id)]),
            )
        except Exception as exc:
            logger.warning("Qdrant delete failed for %s: %s", document_id, exc)

    def semantic_search(
        self,
        query: str,
        *,
        source_types: list[str] | None = None,
        limit: int = 20,
    ) -> list[KnowledgeChunk]:
        self.ensure_collection()
        vector = self._embedder.embed(query)
        query_filter = None
        if source_types:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="source_type",
                        match=qmodels.MatchAny(any=source_types),
                    )
                ]
            )
        try:
            hits = self._get_client().search(
                collection_name=KNOWLEDGE_COLLECTION,
                query_vector=vector,
                query_filter=query_filter,
                limit=limit,
            )
        except Exception as exc:
            logger.warning("Qdrant semantic search failed: %s", exc)
            return []

        chunks: list[KnowledgeChunk] = []
        for hit in hits:
            payload = hit.payload or {}
            chunks.append(
                KnowledgeChunk(
                    document_id=UUID(str(payload.get("document_id", hit.id))),
                    source_type=str(payload.get("source_type", "unknown")),
                    source_id=payload.get("source_id"),
                    title=str(payload.get("title", "")),
                    content=str(payload.get("content", "")),
                    score=float(hit.score or 0),
                    metadata=payload.get("metadata") or {},
                )
            )
        return chunks
