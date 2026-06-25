"""Student Digital Twin & AI Orchestrator endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.digital_twin import (
    DigitalTwinResponse,
    PublishEventRequest,
    PublishEventResponse,
    RefreshResponse,
    TimelineResponse,
)
from app.services.digital_twin.service import DigitalTwinService

router = APIRouter(prefix="/student", tags=["Digital Twin & Orchestrator"])


@router.get("/digital-twin", response_model=DigitalTwinResponse)
async def get_digital_twin(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DigitalTwinResponse:
    """
    Get the unified **Student Digital Twin** — single source of truth for all AI services.

    Aggregates: academic profile, language tests, documents, applications,
    universities, scholarships, recommendations, deadlines, preferences,
    goals, achievements, and weaknesses.

    Also returns the **service registry** of all registered intelligence modules.
    """
    service = DigitalTwinService(db)
    return await service.get_digital_twin(current_user)


@router.get("/timeline", response_model=TimelineResponse)
async def get_student_timeline(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TimelineResponse:
    """
    Chronological student journey timeline.

    Built automatically from platform events (profile updates, document uploads,
    recommendations, application submissions, etc.) plus Redis-cached recent events.
    """
    service = DigitalTwinService(db)
    return await service.get_timeline(current_user, limit=limit)


@router.post("/events", response_model=PublishEventResponse)
async def publish_student_event(
    request: PublishEventRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PublishEventResponse:
    """
    Publish an event to the platform event bus.

    Triggers: twin sync, timeline entry, and optional recommendation refresh.

  **Event types:** `profile.updated`, `document.uploaded`, `recommendation.generated`,
    `application.submitted`, `scholarship.added`, `deadline.passed`, etc.
    """
    service = DigitalTwinService(db)
    return await service.publish_event(current_user, request)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_student_intelligence(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    """
    Refresh all downstream intelligence services from the digital twin.

    Re-runs: **Profile Intelligence**, **University Recommendations**,
    and **Scholarship Matching**, then updates the twin state.
    """
    service = DigitalTwinService(db)
    return await service.refresh(current_user)
