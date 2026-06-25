from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import ApplicationDocument
from app.repositories.base import BaseRepository


class ApplicationDocumentRepository(BaseRepository[ApplicationDocument]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ApplicationDocument)

    async def get_by_application(self, application_id: UUID) -> list[ApplicationDocument]:
        result = await self.db.execute(
            select(ApplicationDocument)
            .where(ApplicationDocument.application_id == application_id)
            .order_by(ApplicationDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_application(
        self, document_id: UUID, application_id: UUID
    ) -> ApplicationDocument | None:
        result = await self.db.execute(
            select(ApplicationDocument).where(
                ApplicationDocument.id == document_id,
                ApplicationDocument.application_id == application_id,
            )
        )
        return result.scalar_one_or_none()
