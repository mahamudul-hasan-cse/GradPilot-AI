"""Activity timeline logging."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import ApplicationActivity
from app.repositories.application_activity import ApplicationActivityRepository


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.repo = ApplicationActivityRepository(db)

    async def log(
        self,
        *,
        application_id: UUID,
        user_id: UUID | None,
        event_type: str,
        title: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ApplicationActivity:
        activity = ApplicationActivity(
            application_id=application_id,
            user_id=user_id,
            event_type=event_type,
            title=title,
            description=description,
            event_metadata=metadata,
        )
        return await self.repo.create(activity)
