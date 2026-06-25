"""Student Digital Twin — unified student state."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StudentDigitalTwin(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "student_digital_twins"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    state_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    academic_profile: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    language_tests: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    documents: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    applications: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    universities: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    scholarships: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    recommendations: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    deadlines: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    preferences: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    goals: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    achievements: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    weaknesses: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TwinEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "twin_events"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    source_service: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    processed: Mapped[bool] = mapped_column(default=False, index=True, nullable=False)


class TwinTimelineEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "twin_timeline"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("twin_events.id", ondelete="SET NULL"))
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    entry_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
