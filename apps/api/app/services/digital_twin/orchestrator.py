"""AI Orchestrator — aggregate, resolve conflicts, trigger downstream services."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.digital_twin import StudentDigitalTwin, TwinEvent
from app.repositories.digital_twin import DigitalTwinRepository, TwinEventRepository
from app.services.digital_twin.aggregator import TwinAggregator
from app.services.digital_twin.event_bus import EventBus
from app.services.digital_twin.refresh_engine import RecommendationRefreshEngine
from app.services.digital_twin.registry import bootstrap_registry
from app.services.digital_twin.timeline_generator import TimelineGenerator
from app.services.digital_twin.types import REFRESH_TRIGGER_EVENTS, TwinEventMessage, TwinEventType

logger = logging.getLogger(__name__)


class AIOrchestrator:
    def __init__(self, db: AsyncSession, event_bus: EventBus | None = None):
        self.db = db
        self.twin_repo = DigitalTwinRepository(db)
        self.event_repo = TwinEventRepository(db)
        self.aggregator = TwinAggregator(db)
        self.timeline = TimelineGenerator(db)
        self.refresh_engine = RecommendationRefreshEngine(db)
        self.event_bus = event_bus or EventBus()
        bootstrap_registry()
        self._setup_subscribers()

    def _setup_subscribers(self) -> None:
        self.event_bus.subscribe("*", self._on_event_timeline)

    async def _on_event_timeline(self, event: TwinEventMessage) -> None:
        await self.timeline.record_from_event(event)

    async def publish_event(
        self,
        *,
        user_id: UUID,
        event_type: str,
        source_service: str,
        payload: dict | None = None,
        auto_refresh: bool = True,
    ) -> TwinEventMessage:
        record = TwinEvent(
            user_id=user_id,
            event_type=event_type,
            source_service=source_service,
            payload=payload or {},
            processed=False,
        )
        record = await self.event_repo.create(record)

        message = TwinEventMessage(
            user_id=user_id,
            event_type=event_type,
            source_service=source_service,
            payload=payload or {},
            event_id=record.id,
            created_at=record.created_at,
        )

        await self.event_bus.publish(message)
        await self.sync_twin(user_id)

        if auto_refresh and event_type in REFRESH_TRIGGER_EVENTS:
            await self.refresh_recommendations(user_id, publish_event=False)

        record.processed = True
        await self.event_repo.update(record)
        return message

    async def sync_twin(self, user_id: UUID) -> StudentDigitalTwin:
        existing = await self.twin_repo.get_by_user_id(user_id)
        version = (existing.version + 1) if existing else 1
        state = await self.aggregator.build_state(user_id, version=version)
        snapshot = state.to_snapshot()

        if existing:
            existing.version = version
            existing.state_snapshot = snapshot
            existing.academic_profile = state.academic_profile
            existing.language_tests = state.language_tests
            existing.documents = state.documents
            existing.applications = state.applications
            existing.universities = state.universities
            existing.scholarships = state.scholarships
            existing.recommendations = state.recommendations
            existing.deadlines = state.deadlines
            existing.preferences = state.preferences
            existing.goals = state.goals
            existing.achievements = state.achievements
            existing.weaknesses = state.weaknesses
            existing.last_synced_at = datetime.now(UTC)
            return await self.twin_repo.update(existing)

        twin = StudentDigitalTwin(
            user_id=user_id,
            version=version,
            state_snapshot=snapshot,
            academic_profile=state.academic_profile,
            language_tests=state.language_tests,
            documents=state.documents,
            applications=state.applications,
            universities=state.universities,
            scholarships=state.scholarships,
            recommendations=state.recommendations,
            deadlines=state.deadlines,
            preferences=state.preferences,
            goals=state.goals,
            achievements=state.achievements,
            weaknesses=state.weaknesses,
            last_synced_at=datetime.now(UTC),
        )
        return await self.twin_repo.create(twin)

    async def refresh_recommendations(self, user_id: UUID, *, publish_event: bool = True) -> dict:
        result = await self.refresh_engine.refresh_all(user_id)
        await self.sync_twin(user_id)
        if publish_event and result.get("refreshed"):
            await self.publish_event(
                user_id=user_id,
                event_type=TwinEventType.TWIN_REFRESHED,
                source_service="digital_twin",
                payload={"refresh_result": result},
                auto_refresh=False,
            )
        return result

    async def get_twin(self, user_id: UUID) -> StudentDigitalTwin:
        twin = await self.twin_repo.get_by_user_id(user_id)
        if twin is None:
            twin = await self.sync_twin(user_id)
        return twin
