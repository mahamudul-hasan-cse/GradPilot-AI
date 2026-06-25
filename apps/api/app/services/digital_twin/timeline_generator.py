"""Chronological timeline generator from twin events."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.digital_twin import TwinTimelineEntry
from app.repositories.digital_twin import TwinTimelineRepository
from app.services.digital_twin.types import TwinEventMessage, TwinEventType

EVENT_TIMELINE_MAP: dict[str, tuple[str, str]] = {
    TwinEventType.PROFILE_UPDATED: ("profile", "Profile updated"),
    TwinEventType.DOCUMENT_UPLOADED: ("documents", "Document uploaded"),
    TwinEventType.DOCUMENT_PARSED: ("documents", "Document parsed"),
    TwinEventType.DOCUMENT_VALIDATED: ("documents", "Document validated"),
    TwinEventType.RECOMMENDATION_GENERATED: ("recommendations", "Recommendations generated"),
    TwinEventType.SCHOLARSHIP_MATCHED: ("scholarships", "Scholarship matches updated"),
    TwinEventType.APPLICATION_CREATED: ("applications", "Application created"),
    TwinEventType.APPLICATION_SUBMITTED: ("applications", "Application submitted"),
    TwinEventType.APPLICATION_STATUS_CHANGED: ("applications", "Application status changed"),
    TwinEventType.SCHOLARSHIP_ADDED: ("scholarships", "Scholarship added"),
    TwinEventType.DEADLINE_PASSED: ("deadlines", "Deadline passed"),
    TwinEventType.DEADLINE_APPROACHING: ("deadlines", "Deadline approaching"),
    TwinEventType.ANALYSIS_COMPLETED: ("intelligence", "Profile analysis completed"),
    TwinEventType.TWIN_REFRESHED: ("system", "Digital twin refreshed"),
    TwinEventType.KNOWLEDGE_QUERY: ("knowledge", "Knowledge query"),
}


class TimelineGenerator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TwinTimelineRepository(db)

    async def record_from_event(self, event: TwinEventMessage) -> TwinTimelineEntry:
        category, default_title = EVENT_TIMELINE_MAP.get(
            event.event_type, ("general", event.event_type.replace(".", " ").title())
        )
        title = event.payload.get("title", default_title)
        description = event.payload.get("description")
        entry = TwinTimelineEntry(
            user_id=event.user_id,
            event_id=event.event_id,
            category=category,
            title=title,
            description=description,
            entry_metadata=event.payload,
            occurred_at=event.created_at or datetime.now(UTC),
        )
        return await self.repo.create(entry)

    async def get_timeline(self, user_id: UUID, *, limit: int = 100) -> list[TwinTimelineEntry]:
        return await self.repo.get_timeline(user_id, limit=limit)
