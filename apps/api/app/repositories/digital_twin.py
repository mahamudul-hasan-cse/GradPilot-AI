from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.digital_twin import StudentDigitalTwin, TwinEvent, TwinTimelineEntry
from app.repositories.base import BaseRepository


class DigitalTwinRepository(BaseRepository[StudentDigitalTwin]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, StudentDigitalTwin)

    async def get_by_user_id(self, user_id: UUID) -> StudentDigitalTwin | None:
        result = await self.db.execute(
            select(StudentDigitalTwin).where(StudentDigitalTwin.user_id == user_id)
        )
        return result.scalar_one_or_none()


class TwinEventRepository(BaseRepository[TwinEvent]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, TwinEvent)

    async def get_unprocessed(self, *, limit: int = 50) -> list[TwinEvent]:
        result = await self.db.execute(
            select(TwinEvent)
            .where(TwinEvent.processed.is_(False))
            .order_by(TwinEvent.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user(self, user_id: UUID, *, limit: int = 50) -> list[TwinEvent]:
        result = await self.db.execute(
            select(TwinEvent)
            .where(TwinEvent.user_id == user_id)
            .order_by(TwinEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class TwinTimelineRepository(BaseRepository[TwinTimelineEntry]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, TwinTimelineEntry)

    async def get_timeline(self, user_id: UUID, *, limit: int = 100) -> list[TwinTimelineEntry]:
        result = await self.db.execute(
            select(TwinTimelineEntry)
            .where(TwinTimelineEntry.user_id == user_id)
            .order_by(TwinTimelineEntry.occurred_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
