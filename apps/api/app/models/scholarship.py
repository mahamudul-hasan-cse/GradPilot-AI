from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Scholarship(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scholarships"

    title: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), index=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(10), default="USD")
    description: Mapped[str | None] = mapped_column(Text)
    eligibility: Mapped[str | None] = mapped_column(Text)
    deadline: Mapped[date | None] = mapped_column(Date)
    application_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    degree_level: Mapped[str | None] = mapped_column(String(50), index=True)
    funding_type: Mapped[str | None] = mapped_column(String(50), index=True)
    minimum_gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), index=True)
    minimum_ielts: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    research_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    work_experience_required_years: Mapped[int | None] = mapped_column(Integer)
    eligible_nationalities: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    eligible_majors: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    university_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("universities.id", ondelete="SET NULL"),
        index=True,
    )
    source_url: Mapped[str | None] = mapped_column(String(1000))
    external_id: Mapped[str | None] = mapped_column(String(255))
