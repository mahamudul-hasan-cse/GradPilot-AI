from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import ApplicationActivity
from app.repositories.base import BaseRepository


class ApplicationActivityRepository(BaseRepository[ApplicationActivity]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ApplicationActivity)

    async def get_timeline(self, application_id: UUID, *, limit: int = 50) -> list[ApplicationActivity]:
        result = await self.db.execute(
            select(ApplicationActivity)
            .where(ApplicationActivity.application_id == application_id)
            .order_by(ApplicationActivity.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
