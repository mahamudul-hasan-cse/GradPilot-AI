"""Deadline tracking and reminder engine."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationDeadline
from app.repositories.application_deadline import ApplicationDeadlineRepository


class DeadlineEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.deadline_repo = ApplicationDeadlineRepository(db)

    async def seed_default_deadlines(self, application: Application) -> list[ApplicationDeadline]:
        created: list[ApplicationDeadline] = []
        existing_deadlines = await self.deadline_repo.get_by_application(application.id)
        existing_types = {d.deadline_type for d in existing_deadlines}

        if application.deadline and "application" not in existing_types:
            created.append(
                await self.deadline_repo.create(
                    ApplicationDeadline(
                        application_id=application.id,
                        deadline_type="application",
                        title="Application Deadline",
                        due_date=application.deadline,
                        reminder_days_before=14,
                    )
                )
            )

        if application.scholarship_id and application.deadline and "scholarship" not in existing_types:
            created.append(
                await self.deadline_repo.create(
                    ApplicationDeadline(
                        application_id=application.id,
                        deadline_type="scholarship",
                        title="Scholarship Deadline",
                        due_date=application.deadline,
                        reminder_days_before=21,
                    )
                )
            )

        return created

    async def get_pending_reminders(self, *, days_ahead: int = 30) -> list[ApplicationDeadline]:
        return await self.deadline_repo.get_due_for_reminder(days_ahead=days_ahead)

    def should_send_reminder(self, deadline: ApplicationDeadline, *, today: date | None = None) -> bool:
        if deadline.is_completed or deadline.reminder_sent_at:
            return False
        today = today or datetime.now(UTC).date()
        reminder_date = deadline.due_date - timedelta(days=deadline.reminder_days_before)
        return today >= reminder_date and today <= deadline.due_date

    async def mark_reminder_sent(self, deadline: ApplicationDeadline) -> ApplicationDeadline:
        deadline.reminder_sent_at = datetime.now(UTC)
        return await self.deadline_repo.update(deadline)
