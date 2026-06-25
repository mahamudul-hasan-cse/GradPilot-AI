from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import ApplicationNote
from app.repositories.base import BaseRepository


class ApplicationNoteRepository(BaseRepository[ApplicationNote]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ApplicationNote)

    async def get_by_application(self, application_id: UUID) -> list[ApplicationNote]:
        result = await self.db.execute(
            select(ApplicationNote)
            .where(ApplicationNote.application_id == application_id)
            .order_by(ApplicationNote.is_pinned.desc(), ApplicationNote.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_application(self, note_id: UUID, application_id: UUID) -> ApplicationNote | None:
        result = await self.db.execute(
            select(ApplicationNote).where(
                ApplicationNote.id == note_id,
                ApplicationNote.application_id == application_id,
            )
        )
        return result.scalar_one_or_none()
