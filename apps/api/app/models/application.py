from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


APPLICATION_STATUSES = frozenset({
    "planning",
    "preparing",
    "ready",
    "submitted",
    "interview",
    "accepted",
    "rejected",
    "deferred",
    "withdrawn",
})

DOCUMENT_TYPES = frozenset({
    "transcript",
    "cv",
    "sop",
    "lor",
    "passport",
    "ielts",
    "financial",
    "other",
})

TASK_TYPES = frozenset({
    "upload_transcript",
    "generate_sop",
    "request_lor",
    "pay_fee",
    "submit_application",
    "visa_application",
    "custom",
})

DEADLINE_TYPES = frozenset({
    "application",
    "scholarship",
    "interview",
    "visa",
    "custom",
})


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    program_id: Mapped[UUID | None] = mapped_column(ForeignKey("programs.id", ondelete="SET NULL"))
    university_id: Mapped[UUID | None] = mapped_column(ForeignKey("universities.id", ondelete="SET NULL"))
    scholarship_id: Mapped[UUID | None] = mapped_column(ForeignKey("scholarships.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(50), default="planning", index=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[date | None] = mapped_column(Date)

    title: Mapped[str | None] = mapped_column(String(255))
    intake_term: Mapped[str | None] = mapped_column(String(50))
    progress_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    progress_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    profile_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    documents_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sop_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lor_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitted_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="applications")
    program: Mapped["Program | None"] = relationship("Program", back_populates="applications")
    university: Mapped["University | None"] = relationship("University")
    scholarship: Mapped["Scholarship | None"] = relationship("Scholarship")
    documents: Mapped[list["ApplicationDocument"]] = relationship(
        "ApplicationDocument", back_populates="application", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["ApplicationTask"]] = relationship(
        "ApplicationTask", back_populates="application", cascade="all, delete-orphan"
    )
    workspace_notes: Mapped[list["ApplicationNote"]] = relationship(
        "ApplicationNote", back_populates="application", cascade="all, delete-orphan"
    )
    activity: Mapped[list["ApplicationActivity"]] = relationship(
        "ApplicationActivity", back_populates="application", cascade="all, delete-orphan"
    )
    deadlines: Mapped[list["ApplicationDeadline"]] = relationship(
        "ApplicationDeadline", back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_documents"

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(500))
    file_url: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    application: Mapped["Application"] = relationship("Application", back_populates="documents")


class ApplicationTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_tasks"

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    application: Mapped["Application"] = relationship("Application", back_populates="tasks")


class ApplicationNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_notes"

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    application: Mapped["Application"] = relationship("Application", back_populates="workspace_notes")


class ApplicationActivity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_activity"

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)

    application: Mapped["Application"] = relationship("Application", back_populates="activity")


class ApplicationDeadline(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_deadlines"

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    deadline_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    reminder_days_before: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    application: Mapped["Application"] = relationship("Application", back_populates="deadlines")
