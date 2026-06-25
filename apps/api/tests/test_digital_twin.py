"""Tests for Student Digital Twin & AI Orchestrator."""

from uuid import uuid4

import pytest

from app.services.digital_twin.event_bus import EventBus
from app.services.digital_twin.registry import ServiceRegistry, bootstrap_registry
from app.services.digital_twin.types import REFRESH_TRIGGER_EVENTS, TwinEventType, TwinState


class TestServiceRegistry:
    def setup_method(self):
        ServiceRegistry.clear()

    def test_bootstrap_registers_services(self):
        bootstrap_registry()
        services = ServiceRegistry.list_services()
        names = {s.name for s in services}
        assert "profile_intelligence" in names
        assert "university_recommendation" in names
        assert "scholarship_matching" in names
        assert "knowledge_platform" in names
        assert "application_workspace" in names
        assert "digital_twin" in names

    def test_get_service(self):
        bootstrap_registry()
        svc = ServiceRegistry.get("profile_intelligence")
        assert svc is not None
        assert "analyze" in svc.capabilities


class TestTwinState:
    def test_to_snapshot(self):
        state = TwinState(
            user_id=uuid4(),
            version=1,
            academic_profile={"cgpa": 3.5},
            language_tests={"ielts": 7.0},
            documents=[],
            applications=[],
            universities=[],
            scholarships=[],
            recommendations={},
            deadlines=[],
            preferences={},
            goals=[],
            achievements=[],
            weaknesses=[],
        )
        snapshot = state.to_snapshot()
        assert snapshot["version"] == 1
        assert snapshot["academic_profile"]["cgpa"] == 3.5


class TestEventTypes:
    def test_refresh_triggers_include_profile_updated(self):
        assert TwinEventType.PROFILE_UPDATED in REFRESH_TRIGGER_EVENTS

    def test_event_type_values(self):
        assert TwinEventType.APPLICATION_SUBMITTED == "application.submitted"


class TestEventBus:
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        bus = EventBus()
        bus._enabled = False
        received = []

        async def handler(event):
            received.append(event.event_type)

        bus.subscribe("profile.updated", handler)
        from app.services.digital_twin.types import TwinEventMessage

        await bus.publish(
            TwinEventMessage(
                user_id=uuid4(),
                event_type="profile.updated",
                source_service="test",
                payload={},
            )
        )
        assert "profile.updated" in received
