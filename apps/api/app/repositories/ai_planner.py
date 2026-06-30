from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_planner import PlannerHistory, PlannerNotification, PlannerSchedule, PlannerTask
from app.repositories.base import BaseRepository


class PlannerHistoryRepository(BaseRepository[PlannerHistory]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, PlannerHistory)

    async def get_latest_for_user(self, user_id: UUID) -> PlannerHistory | None:
        result = await self.db.execute(
            select(PlannerHistory)
            .where(PlannerHistory.user_id == user_id)
            .order_by(PlannerHistory.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_all(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(PlannerHistory))
        return result.scalar_one() or 0


class PlannerTaskRepository(BaseRepository[PlannerTask]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, PlannerTask)

    async def get_by_plan(self, plan_id: UUID) -> list[PlannerTask]:
        result = await self.db.execute(
            select(PlannerTask)
            .where(PlannerTask.plan_id == plan_id)
            .order_by(PlannerTask.priority_rank.asc().nullslast())
        )
        return list(result.scalars().all())

    async def get_by_user_and_horizon(self, user_id: UUID, horizon: str) -> list[PlannerTask]:
        result = await self.db.execute(
            select(PlannerTask)
            .where(PlannerTask.user_id == user_id, PlannerTask.time_horizon == horizon)
            .order_by(PlannerTask.priority_rank.asc().nullslast())
        )
        return list(result.scalars().all())

    async def delete_by_plan(self, plan_id: UUID) -> None:
        tasks = await self.get_by_plan(plan_id)
        for task in tasks:
            await self.delete(task)


class PlannerScheduleRepository(BaseRepository[PlannerSchedule]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, PlannerSchedule)

    async def get_by_plan(self, plan_id: UUID) -> list[PlannerSchedule]:
        result = await self.db.execute(
            select(PlannerSchedule)
            .where(PlannerSchedule.plan_id == plan_id)
            .order_by(PlannerSchedule.start_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_user_range(self, user_id: UUID, start, end) -> list[PlannerSchedule]:
        result = await self.db.execute(
            select(PlannerSchedule)
            .where(
                PlannerSchedule.user_id == user_id,
                PlannerSchedule.start_at >= start,
                PlannerSchedule.start_at <= end,
            )
            .order_by(PlannerSchedule.start_at.asc())
        )
        return list(result.scalars().all())


class PlannerNotificationRepository(BaseRepository[PlannerNotification]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, PlannerNotification)

    async def get_unread(self, user_id: UUID, *, limit: int = 50) -> list[PlannerNotification]:
        result = await self.db.execute(
            select(PlannerNotification)
            .where(PlannerNotification.user_id == user_id, PlannerNotification.is_read.is_(False))
            .order_by(PlannerNotification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_type(self, user_id: UUID, notification_type: str) -> list[PlannerNotification]:
        result = await self.db.execute(
            select(PlannerNotification)
            .where(
                PlannerNotification.user_id == user_id,
                PlannerNotification.notification_type == notification_type,
            )
            .order_by(PlannerNotification.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_type(self) -> dict[str, int]:
        result = await self.db.execute(
            select(PlannerNotification.notification_type, func.count())
            .group_by(PlannerNotification.notification_type)
        )
        return {row[0]: row[1] for row in result.all()}
