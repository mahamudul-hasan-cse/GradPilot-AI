"""Admin analytics for application workspace."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.university import University
from app.repositories.application_deadline import ApplicationDeadlineRepository


class ApplicationAnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.deadline_repo = ApplicationDeadlineRepository(db)

    async def get_dashboard(self) -> dict:
        total = await self.db.scalar(select(func.count()).select_from(Application)) or 0

        status_rows = await self.db.execute(
            select(Application.status, func.count()).group_by(Application.status)
        )
        status_distribution = {row[0]: row[1] for row in status_rows.all()}

        accepted = status_distribution.get("accepted", 0)
        rejected = status_distribution.get("rejected", 0)
        decided = accepted + rejected
        acceptance_rate = round(accepted / max(decided, 1) * 100, 2)

        avg_progress = await self.db.scalar(select(func.avg(Application.progress_percent)))
        completion_rate = round(float(avg_progress or 0), 2)

        country_rows = await self.db.execute(
            select(University.country, func.count())
            .join(Application, Application.university_id == University.id)
            .group_by(University.country)
            .order_by(func.count().desc())
            .limit(15)
        )
        country_distribution = {row[0]: row[1] for row in country_rows.all()}

        recent = await self.db.execute(
            select(Application).order_by(Application.created_at.desc()).limit(10)
        )
        recent_apps = [
            {
                "id": str(a.id),
                "status": a.status,
                "progress_percent": float(a.progress_percent or 0),
                "title": a.title,
                "created_at": a.created_at.isoformat(),
            }
            for a in recent.scalars().all()
        ]

        upcoming_deadlines = await self.deadline_repo.count_upcoming()

        return {
            "total_applications": total,
            "status_distribution": status_distribution,
            "acceptance_rate": acceptance_rate,
            "completion_rate": completion_rate,
            "country_distribution": country_distribution,
            "university_distribution": country_distribution,
            "upcoming_deadlines": upcoming_deadlines,
            "recent_applications": recent_apps,
        }
