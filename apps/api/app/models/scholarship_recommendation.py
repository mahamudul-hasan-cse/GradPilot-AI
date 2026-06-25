"""Scholarship recommendation history."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ScholarshipRecommendationHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scholarship_recommendation_history"

    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    cache_key: Mapped[str | None] = mapped_column(String(64), index=True)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    response_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    avg_scholarship_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    avg_eligibility_probability: Mapped[float | None] = mapped_column(Numeric(5, 4))
    excellent_count: Mapped[int] = mapped_column(default=0)
    strong_count: Mapped[int] = mapped_column(default=0)
    possible_count: Mapped[int] = mapped_column(default=0)
    low_count: Mapped[int] = mapped_column(default=0)
    candidates_evaluated: Mapped[int] = mapped_column(default=0)
    cache_hit: Mapped[bool] = mapped_column(default=False)
