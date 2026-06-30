"""AI Planner API schemas."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlannerGenerateRequest(BaseModel):
    use_cache: bool = True
    force_regenerate: bool = False
    horizon_days: int = Field(default=30, ge=7, le=90)


class ExplainedItem(BaseModel):
    title: str
    description: str | None = None
    reason: str
    priority_score: float | None = None
    category: str | None = None
    due_date: date | None = None


class PlannerTaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    category: str
    task_type: str
    source: str
    reason: str
    priority_score: float
    priority_rank: int | None
    status: str
    due_date: date | None
    scheduled_date: date | None
    time_horizon: str | None

    model_config = {"from_attributes": True}


class PlannerScheduleResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    schedule_type: str
    reason: str
    start_at: datetime
    end_at: datetime | None
    task_id: UUID | None

    model_config = {"from_attributes": True}


class PlannerNotificationResponse(BaseModel):
    id: UUID
    notification_type: str
    title: str
    message: str
    reason: str
    severity: str
    is_read: bool
    scheduled_for: datetime | None

    model_config = {"from_attributes": True}


class ReadinessMilestone(BaseModel):
    label: str
    target_date: date
    readiness_percent: float
    reason: str


class PlannerPlanResponse(BaseModel):
    plan_id: UUID
    priority_score: float
    cache_hit: bool = False
    twin_version: int
    todays_tasks: list[PlannerTaskResponse]
    tomorrows_tasks: list[PlannerTaskResponse]
    weekly_goals: list[ExplainedItem]
    monthly_roadmap: list[ExplainedItem]
    missing_requirements: list[ExplainedItem]
    risk_alerts: list[ExplainedItem]
    deadline_alerts: list[ExplainedItem]
    readiness_timeline: list[ReadinessMilestone]
    progress_prediction: dict[str, float]
    generated_at: datetime


class PlannerCalendarResponse(BaseModel):
    entries: list[PlannerScheduleResponse]
    start: datetime
    end: datetime


class PlannerDigestResponse(BaseModel):
    digest_type: str
    title: str
    summary: str
    highlights: list[ExplainedItem]
    tasks_due: list[PlannerTaskResponse]
    alerts: list[PlannerNotificationResponse]
    generated_at: datetime


class PlannerAnalyticsResponse(BaseModel):
    total_plans_generated: int
    total_tasks_created: int
    total_notifications: int
    notifications_by_type: dict[str, int]
    average_priority_score: float
    cache_hit_rate: float
    top_task_categories: dict[str, int]
