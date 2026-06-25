from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class University(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "universities"

    name: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    city: Mapped[str | None] = mapped_column(String(100))
    website: Mapped[str | None] = mapped_column(String(500))
    ranking: Mapped[int | None] = mapped_column(Integer, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tuition_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), index=True)
    application_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    minimum_gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), index=True)
    minimum_ielts: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    minimum_toefl: Mapped[int | None] = mapped_column(Integer)
    deadline: Mapped[date | None] = mapped_column(Date)
    programs: Mapped[list[str] | None] = mapped_column(JSON)
    scholarships_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    search_text: Mapped[str | None] = mapped_column(Text)
    majors: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    last_ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    data_quality_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    program_records: Mapped[list["Program"]] = relationship(
        "Program",
        back_populates="university",
        cascade="all, delete-orphan",
    )

    def build_search_text(self) -> str:
        parts = [
            self.name,
            self.country,
            self.city or "",
            self.description or "",
            " ".join(self.programs or []),
            " ".join(self.majors or []),
        ]
        return " ".join(p for p in parts if p).strip()


class Program(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "programs"

    university_id: Mapped[UUID] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    degree_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    field_of_study: Mapped[str | None] = mapped_column(String(255))
    duration_months: Mapped[int | None] = mapped_column(Integer)
    tuition_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    tuition_currency: Mapped[str | None] = mapped_column(String(10), default="USD")
    language: Mapped[str | None] = mapped_column(String(50), default="English")
    description: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    application_deadline: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    university: Mapped["University"] = relationship("University", back_populates="program_records")
    applications: Mapped[list["Application"]] = relationship(
        "Application",
        back_populates="program",
    )
