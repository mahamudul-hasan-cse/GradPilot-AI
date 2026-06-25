from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import ApplicationTask
from app.repositories.base import BaseRepository


class ApplicationTaskRepository(BaseRepository[ApplicationTask]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ApplicationTask)

    async def get_by_application(self, application_id: UUID) -> list[ApplicationTask]:
        result = await self.db.execute(
            select(ApplicationTask)
            .where(ApplicationTask.application_id == application_id)
            .order_by(ApplicationTask.sort_order, ApplicationTask.created_at)
        )
        return list(result.scalars().all())

    async def get_for_application(self, task_id: UUID, application_id: UUID) -> ApplicationTask | None:
        result = await self.db.execute(
            select(ApplicationTask).where(
                ApplicationTask.id == task_id,
                ApplicationTask.application_id == application_id,
            )
        )
        return result.scalar_one_or_none()
