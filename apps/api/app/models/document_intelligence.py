"""Document Intelligence Platform models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

SUPPORTED_DOCUMENT_TYPES = frozenset({
    "passport",
    "transcript",
    "degree_certificate",
    "cv",
    "ielts_trf",
    "toefl",
    "gre",
    "lor",
    "sop",
})

DOCUMENT_STATUSES = frozenset({
    "uploaded",
    "queued",
    "processing",
    "parsed",
    "validated",
    "failed",
    "duplicate",
})


class DocumentUpload(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_uploads"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    application_id: Mapped[UUID | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"))
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("document_uploads.id", ondelete="SET NULL"))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(50), index=True)
    classified_type: Mapped[str | None] = mapped_column(String(50))
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(1000))
    file_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", index=True, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    extracted_fields: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    validation_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_of_id: Mapped[UUID | None] = mapped_column(ForeignKey("document_uploads.id", ondelete="SET NULL"))
    processing_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class DocumentProcessingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_processing_jobs"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_uploads.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)
    stage: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)
    queue_position: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
