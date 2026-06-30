"""AI Planner internal types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class PlannerTaskDraft:
    title: str
    description: str | None
    category: str
    task_type: str
    source: str
    reason: str
    priority_score: float = 0.5
    due_date: date | None = None
    scheduled_date: date | None = None
    time_horizon: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlannerScheduleDraft:
    title: str
    description: str | None
    schedule_type: str
    reason: str
    start_at: Any
    end_at: Any | None = None
    task_index: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlannerNotificationDraft:
    notification_type: str
    title: str
    message: str
    reason: str
    severity: str = "info"
    scheduled_for: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlannerPlanDraft:
    priority_score: float
    tasks: list[PlannerTaskDraft]
    schedule: list[PlannerScheduleDraft]
    notifications: list[PlannerNotificationDraft]
    weekly_goals: list[dict[str, Any]]
    monthly_roadmap: list[dict[str, Any]]
    missing_requirements: list[dict[str, Any]]
    risk_alerts: list[dict[str, Any]]
    deadline_alerts: list[dict[str, Any]]
    readiness_timeline: list[dict[str, Any]]
    progress_prediction: dict[str, float]
