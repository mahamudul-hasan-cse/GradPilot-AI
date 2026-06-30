"""AI Planner REST API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai_planner import (
    PlannerAnalyticsResponse,
    PlannerCalendarResponse,
    PlannerDigestResponse,
    PlannerGenerateRequest,
    PlannerNotificationResponse,
    PlannerPlanResponse,
    PlannerTaskResponse,
)
from app.services.ai_planner.service import PlannerService

router = APIRouter(prefix="/planner", tags=["AI Planner"])


@router.post("/generate", response_model=PlannerPlanResponse)
async def generate_plan(
    request: PlannerGenerateRequest | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlannerPlanResponse:
    """
    Generate a personalized study-abroad action plan from the Student Digital Twin.

    Consumes profile analysis, recommendations, scholarships, documents,
    deadlines, timeline, and applications. Every task includes a **reason** explaining why it was generated.
    """
    service = PlannerService(db)
    return await service.generate_plan(current_user.id, request)


@router.post("/regenerate", response_model=PlannerPlanResponse)
async def regenerate_plan(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlannerPlanResponse:
    """Force-regenerate the plan from the latest Digital Twin state."""
    service = PlannerService(db)
    return await service.regenerate(current_user.id, reason="manual_regenerate")


@router.get("/plan", response_model=PlannerPlanResponse)
async def get_current_plan(
    use_cache: bool = Query(default=True),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlannerPlanResponse:
    """Get the current study plan (generates if none exists)."""
    service = PlannerService(db)
    return await service.generate_plan(current_user.id, PlannerGenerateRequest(use_cache=use_cache))


@router.get("/tasks/today", response_model=list[PlannerTaskResponse])
async def get_todays_tasks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PlannerTaskResponse]:
    """Today's prioritized tasks."""
    service = PlannerService(db)
    plan = await service.generate_plan(current_user.id)
    return plan.todays_tasks


@router.get("/tasks/tomorrow", response_model=list[PlannerTaskResponse])
async def get_tomorrows_tasks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PlannerTaskResponse]:
    """Tomorrow's prioritized tasks."""
    service = PlannerService(db)
    plan = await service.generate_plan(current_user.id)
    return plan.tomorrows_tasks


@router.get("/weekly-goals", response_model=PlannerPlanResponse)
async def get_weekly_goals(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlannerPlanResponse:
    """Weekly goals with explanations."""
    service = PlannerService(db)
    return await service.generate_plan(current_user.id)


@router.get("/calendar", response_model=PlannerCalendarResponse)
async def get_calendar(
    days: int = Query(default=14, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlannerCalendarResponse:
    """Calendar view of scheduled planner entries."""
    service = PlannerService(db)
    return await service.get_calendar(current_user.id, days=days)


@router.get("/digest/daily", response_model=PlannerDigestResponse)
async def get_daily_digest(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlannerDigestResponse:
    """Daily digest with today's tasks and alerts."""
    service = PlannerService(db)
    return await service.get_daily_digest(current_user.id)


@router.get("/digest/weekly", response_model=PlannerDigestResponse)
async def get_weekly_digest(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlannerDigestResponse:
    """Weekly planning digest."""
    service = PlannerService(db)
    return await service.get_weekly_digest(current_user.id)


@router.get("/notifications", response_model=list[PlannerNotificationResponse])
async def get_notifications(
    unread_only: bool = Query(default=True),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PlannerNotificationResponse]:
    """Planner notifications including risk and deadline alerts."""
    service = PlannerService(db)
    if unread_only:
        notifs = await service.notification_repo.get_unread(current_user.id)
    else:
        notifs = await service.notification_repo.get_by_type(current_user.id, "risk_alert")
        notifs += await service.notification_repo.get_by_type(current_user.id, "deadline_alert")
    return [PlannerNotificationResponse.model_validate(n) for n in notifs]


@router.get("/analytics", response_model=PlannerAnalyticsResponse)
async def get_planner_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PlannerAnalyticsResponse:
    """Admin analytics for the AI Planner module."""
    service = PlannerService(db)
    return await service.get_analytics()
