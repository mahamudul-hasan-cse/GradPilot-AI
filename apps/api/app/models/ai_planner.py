"""AI Planner models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PlannerHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "planner_history"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    cache_key: Mapped[str | None] = mapped_column(String(128), index=True)
    twin_version: Mapped[int] = mapped_column(Integer, default=1)
    priority_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    readiness_timeline: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    response_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)


class PlannerTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "planner_tasks"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("planner_history.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), default="action")
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority_score: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    priority_rank: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    due_date: Mapped[date | None] = mapped_column(Date)
    scheduled_date: Mapped[date | None] = mapped_column(Date, index=True)
    time_horizon: Mapped[str | None] = mapped_column(String(20))
    task_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class PlannerSchedule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "planner_schedule"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("planner_history.id", ondelete="CASCADE"))
    task_id: Mapped[UUID | None] = mapped_column(ForeignKey("planner_tasks.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    schedule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    schedule_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class PlannerNotification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "planner_notifications"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("planner_history.id", ondelete="SET NULL"))
    notification_type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notification_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
