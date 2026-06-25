from uuid import UUID

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_document import KnowledgeDocument
from app.repositories.base import BaseRepository


class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, KnowledgeDocument)

    async def keyword_search(
        self,
        query: str,
        *,
        source_types: list[str] | None = None,
        limit: int = 30,
    ) -> list[tuple[KnowledgeDocument, float]]:
        ts_query = query.strip()
        if not ts_query:
            return []

        stmt = (
            select(
                KnowledgeDocument,
                func.ts_rank_cd(
                    func.to_tsvector("english", KnowledgeDocument.title + " " + KnowledgeDocument.content),
                    func.plainto_tsquery("english", ts_query),
                ).label("rank"),
            )
            .where(KnowledgeDocument.is_active.is_(True))
            .where(
                func.to_tsvector("english", KnowledgeDocument.title + " " + KnowledgeDocument.content).op("@@")(
                    func.plainto_tsquery("english", ts_query)
                )
            )
        )

        if source_types:
            stmt = stmt.where(KnowledgeDocument.source_type.in_(source_types))

        stmt = stmt.order_by(text("rank DESC")).limit(limit)
        result = await self.db.execute(stmt)
        return [(row[0], float(row[1] or 0)) for row in result.all()]

    async def fallback_ilike_search(
        self,
        query: str,
        *,
        source_types: list[str] | None = None,
        limit: int = 30,
    ) -> list[KnowledgeDocument]:
        pattern = f"%{query}%"
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.is_active.is_(True),
            or_(
                KnowledgeDocument.title.ilike(pattern),
                KnowledgeDocument.content.ilike(pattern),
            ),
        )
        if source_types:
            stmt = stmt.where(KnowledgeDocument.source_type.in_(source_types))
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ids(self, ids: list[UUID]) -> list[KnowledgeDocument]:
        if not ids:
            return []
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id.in_(ids))
        )
        docs = {d.id: d for d in result.scalars().all()}
        return [docs[i] for i in ids if i in docs]

    async def get_by_source(self, source_type: str, source_id: str) -> list[KnowledgeDocument]:
        result = await self.db.execute(
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.source_type == source_type,
                KnowledgeDocument.source_id == source_id,
                KnowledgeDocument.is_active.is_(True),
            )
            .order_by(KnowledgeDocument.chunk_index)
        )
        return list(result.scalars().all())

    async def count_active(self) -> int:
        return await self.db.scalar(
            select(func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.is_active.is_(True))
        ) or 0

    async def delete_by_source(self, source_type: str, source_id: str) -> None:
        from sqlalchemy import delete

        await self.db.execute(
            delete(KnowledgeDocument).where(
                KnowledgeDocument.source_type == source_type,
                KnowledgeDocument.source_id == source_id,
            )
        )
