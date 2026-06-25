"""Digital Twin service — public API layer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.digital_twin import TwinTimelineRepository
from app.schemas.digital_twin import (
    DigitalTwinResponse,
    PublishEventRequest,
    PublishEventResponse,
    RefreshResponse,
    RegisteredServiceResponse,
    TimelineEntryResponse,
    TimelineResponse,
)
from app.services.digital_twin.event_bus import EventBus
from app.services.digital_twin.orchestrator import AIOrchestrator
from app.services.digital_twin.registry import ServiceRegistry, bootstrap_registry

# Shared event bus instance for cross-request pub/sub
_global_event_bus = EventBus()


class DigitalTwinService:
    def __init__(self, db: AsyncSession, event_bus: EventBus | None = None):
        self.db = db
        self.orchestrator = AIOrchestrator(db, event_bus=event_bus or _global_event_bus)
        self.timeline_repo = TwinTimelineRepository(db)
        bootstrap_registry()

    async def get_digital_twin(self, user: User) -> DigitalTwinResponse:
        twin = await self.orchestrator.get_twin(user.id)
        return DigitalTwinResponse(
            user_id=twin.user_id,
            version=twin.version,
            state_snapshot=twin.state_snapshot,
            academic_profile=twin.academic_profile or {},
            language_tests=twin.language_tests or {},
            documents=twin.documents or [],
            applications=twin.applications or [],
            universities=twin.universities or [],
            scholarships=twin.scholarships or [],
            recommendations=twin.recommendations or {},
            deadlines=twin.deadlines or [],
            preferences=twin.preferences or {},
            goals=twin.goals or [],
            achievements=twin.achievements or [],
            weaknesses=twin.weaknesses or [],
            last_synced_at=twin.last_synced_at,
            registered_services=[
                RegisteredServiceResponse(
                    name=s.name,
                    description=s.description,
                    version=s.version,
                    capabilities=s.capabilities,
                )
                for s in ServiceRegistry.list_services()
            ],
        )

    async def get_timeline(self, user: User, *, limit: int = 100) -> TimelineResponse:
        entries = await self.orchestrator.timeline.get_timeline(user.id, limit=limit)
        recent_events = await self.orchestrator.event_bus.get_recent(user.id, limit=20)
        return TimelineResponse(
            entries=[
                TimelineEntryResponse(
                    id=e.id,
                    category=e.category,
                    title=e.title,
                    description=e.description,
                    metadata=e.entry_metadata,
                    occurred_at=e.occurred_at,
                )
                for e in entries
            ],
            total=len(entries),
            recent_events=recent_events,
        )

    async def publish_event(self, user: User, request: PublishEventRequest) -> PublishEventResponse:
        message = await self.orchestrator.publish_event(
            user_id=user.id,
            event_type=request.event_type,
            source_service=request.source_service,
            payload=request.payload,
            auto_refresh=request.auto_refresh,
        )
        twin = await self.orchestrator.get_twin(user.id)
        return PublishEventResponse(
            event_id=message.event_id,
            event_type=message.event_type,
            processed=True,
            twin_version=twin.version,
        )

    async def refresh(self, user: User) -> RefreshResponse:
        result = await self.orchestrator.refresh_recommendations(user.id)
        twin = await self.orchestrator.get_twin(user.id)
        return RefreshResponse(
            refreshed=result.get("refreshed", False),
            services=result.get("services", {}),
            twin_version=twin.version,
            reason=result.get("reason"),
        )
