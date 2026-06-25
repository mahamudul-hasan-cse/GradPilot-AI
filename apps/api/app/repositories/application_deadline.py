from datetime import date, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import ApplicationDeadline
from app.repositories.base import BaseRepository


class ApplicationDeadlineRepository(BaseRepository[ApplicationDeadline]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ApplicationDeadline)

    async def get_by_application(self, application_id) -> list[ApplicationDeadline]:
        result = await self.db.execute(
            select(ApplicationDeadline)
            .where(ApplicationDeadline.application_id == application_id)
            .order_by(ApplicationDeadline.due_date)
        )
        return list(result.scalars().all())

    async def get_for_application(self, deadline_id, application_id) -> ApplicationDeadline | None:
        result = await self.db.execute(
            select(ApplicationDeadline).where(
                ApplicationDeadline.id == deadline_id,
                ApplicationDeadline.application_id == application_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_due_for_reminder(self, *, days_ahead: int = 30) -> list[ApplicationDeadline]:
        today = date.today()
        horizon = today + timedelta(days=days_ahead)
        result = await self.db.execute(
            select(ApplicationDeadline).where(
                ApplicationDeadline.is_completed.is_(False),
                ApplicationDeadline.reminder_sent_at.is_(None),
                ApplicationDeadline.due_date >= today,
                ApplicationDeadline.due_date <= horizon,
            )
        )
        return list(result.scalars().all())

    async def count_upcoming(self) -> int:
        today = date.today()
        return (
            await self.db.scalar(
                select(func.count())
                .select_from(ApplicationDeadline)
                .where(
                    ApplicationDeadline.is_completed.is_(False),
                    ApplicationDeadline.due_date >= today,
                )
            )
            or 0
        )
