"""Profile analysis history."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProfileAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "profile_analysis"

    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    cache_key: Mapped[str | None] = mapped_column(String(128), index=True)
    analyzer_type: Mapped[str] = mapped_column(String(50), default="rule_based", index=True)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    response_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    admission_readiness_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    scholarship_readiness_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    employability_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    recommended_university_tier: Mapped[str | None] = mapped_column(String(100))
    cache_hit: Mapped[bool] = mapped_column(default=False)
