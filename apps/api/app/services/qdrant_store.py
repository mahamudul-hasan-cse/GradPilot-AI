"""Qdrant vector store for university semantic search."""

from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import settings
from app.services.embedding import VECTOR_SIZE, get_embedding_provider

UNIVERSITY_COLLECTION = "universities"


class QdrantVectorStore:
    def __init__(self, client: QdrantClient | None = None) -> None:
        self._client = client or QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self._embeddings = get_embedding_provider()

    def ensure_collection(self) -> None:
        collections = {c.name for c in self._client.get_collections().collections}
        if UNIVERSITY_COLLECTION not in collections:
            self._client.create_collection(
                collection_name=UNIVERSITY_COLLECTION,
                vectors_config=qmodels.VectorParams(
                    size=VECTOR_SIZE,
                    distance=qmodels.Distance.COSINE,
                ),
            )

    def upsert_university(
        self,
        university_id: UUID,
        *,
        name: str,
        country: str,
        search_text: str,
        payload: dict | None = None,
    ) -> None:
        self.ensure_collection()
        text = search_text or f"{name} {country}"
        vector = self._embeddings.embed(text)
        point_payload = {
            "university_id": str(university_id),
            "name": name,
            "country": country,
            **(payload or {}),
        }
        self._client.upsert(
            collection_name=UNIVERSITY_COLLECTION,
            points=[
                qmodels.PointStruct(
                    id=str(university_id),
                    vector=vector,
                    payload=point_payload,
                )
            ],
        )

    def semantic_search(
        self,
        query: str,
        *,
        limit: int = 10,
        country: str | None = None,
    ) -> list[tuple[UUID, float]]:
        self.ensure_collection()
        vector = self._embeddings.embed(query)

        query_filter = None
        if country:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="country",
                        match=qmodels.MatchText(text=country),
                    )
                ]
            )

        try:
            results = self._client.search(
                collection_name=UNIVERSITY_COLLECTION,
                query_vector=vector,
                limit=limit,
                query_filter=query_filter,
            )
        except Exception:
            return []

        output: list[tuple[UUID, float]] = []
        for hit in results:
            uid = hit.payload.get("university_id") if hit.payload else None
            if uid:
                output.append((UUID(uid), hit.score))
        return output

    def delete_university(self, university_id: UUID) -> None:
        try:
            self._client.delete(
                collection_name=UNIVERSITY_COLLECTION,
                points_selector=qmodels.PointIdsList(points=[str(university_id)]),
            )
        except Exception:
            pass
