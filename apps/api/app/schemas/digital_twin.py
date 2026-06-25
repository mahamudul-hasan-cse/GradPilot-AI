from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RegisteredServiceResponse(BaseModel):
    name: str
    description: str
    version: str
    capabilities: list[str]


class DigitalTwinResponse(BaseModel):
    user_id: UUID
    version: int
    state_snapshot: dict[str, Any]
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
    weaknesses: list[Any]
    last_synced_at: datetime | None
    registered_services: list[RegisteredServiceResponse] = Field(default_factory=list)


class TimelineEntryResponse(BaseModel):
    id: UUID
    category: str
    title: str
    description: str | None
    metadata: dict[str, Any] | None = None
    occurred_at: datetime


class TimelineResponse(BaseModel):
    entries: list[TimelineEntryResponse]
    total: int
    recent_events: list[dict[str, Any]] = Field(default_factory=list)


class PublishEventRequest(BaseModel):
    event_type: str = Field(
        description="Event type e.g. profile.updated, application.submitted",
    )
    source_service: str = Field(description="Originating service name")
    payload: dict[str, Any] = Field(default_factory=dict)
    auto_refresh: bool = Field(
        default=True,
        description="Auto-refresh recommendations on profile-changing events",
    )


class PublishEventResponse(BaseModel):
    event_id: UUID | None
    event_type: str
    processed: bool
    twin_version: int


class RefreshResponse(BaseModel):
    refreshed: bool
    services: dict[str, Any] = Field(default_factory=dict)
    twin_version: int
    reason: str | None = None
