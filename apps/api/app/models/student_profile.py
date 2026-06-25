from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StudentProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    nationality: Mapped[str | None] = mapped_column(String(100))
    current_country: Mapped[str | None] = mapped_column(String(100))
    education_level: Mapped[str | None] = mapped_column(String(100))
    field_of_study: Mapped[str | None] = mapped_column(String(255))
    gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    gpa_scale: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), default=Decimal("4.0"))
    target_degree: Mapped[str | None] = mapped_column(String(100))
    target_countries: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    budget_currency: Mapped[str | None] = mapped_column(String(10), default="USD")
    test_scores: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    work_experience_years: Mapped[int | None] = mapped_column(Integer)
    bio: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship("User", back_populates="profile")
