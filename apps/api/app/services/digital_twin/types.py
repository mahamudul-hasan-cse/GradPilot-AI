"""Digital twin types and event definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class TwinEventType(StrEnum):
    PROFILE_UPDATED = "profile.updated"
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PARSED = "document.parsed"
    DOCUMENT_VALIDATED = "document.validated"
    RECOMMENDATION_GENERATED = "recommendation.generated"
    SCHOLARSHIP_MATCHED = "scholarship.matched"
    APPLICATION_CREATED = "application.created"
    APPLICATION_SUBMITTED = "application.submitted"
    APPLICATION_STATUS_CHANGED = "application.status_changed"
    SCHOLARSHIP_ADDED = "scholarship.added"
    DEADLINE_PASSED = "deadline.passed"
    DEADLINE_APPROACHING = "deadline.approaching"
    ANALYSIS_COMPLETED = "analysis.completed"
    TWIN_REFRESHED = "twin.refreshed"
    KNOWLEDGE_QUERY = "knowledge.query"


REFRESH_TRIGGER_EVENTS = frozenset({
    TwinEventType.PROFILE_UPDATED,
    TwinEventType.DOCUMENT_UPLOADED,
    TwinEventType.APPLICATION_SUBMITTED,
    TwinEventType.ANALYSIS_COMPLETED,
})


@dataclass
class TwinEventMessage:
    user_id: UUID
    event_type: str
    source_service: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: UUID | None = None
    created_at: datetime | None = None


@dataclass
class TwinState:
    user_id: UUID
    version: int
    academic_profile: dict[str, Any]
    language_tests: dict[str, Any]
    documents: list[dict[str, Any]]
    applications: list[dict[str, Any]]
    universities: list[dict[str, Any]]
    scholarships: list[dict[str, Any]]
    recommendations: dict[str, Any]
    deadlines: list[dict[str, Any]]
    preferences: dict[str, Any]
    goals: list[dict[str, Any]]
    achievements: list[dict[str, Any]]
    weaknesses: list[dict[str, Any]]
    last_synced_at: str | None = None

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "version": self.version,
            "academic_profile": self.academic_profile,
            "language_tests": self.language_tests,
            "documents": self.documents,
            "applications": self.applications,
            "universities": self.universities,
            "scholarships": self.scholarships,
            "recommendations": self.recommendations,
            "deadlines": self.deadlines,
            "preferences": self.preferences,
            "goals": self.goals,
            "achievements": self.achievements,
            "weaknesses": self.weaknesses,
            "last_synced_at": self.last_synced_at,
        }
