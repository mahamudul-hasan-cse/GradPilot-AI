"""Ingestion pipeline ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IngestionSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Catalog of university URLs to scrape (supports 10k+ scale)."""

    __tablename__ = "ingestion_sources"
    __table_args__ = (UniqueConstraint("source_url", name="uq_ingestion_sources_url"),)

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(100), index=True)
    city: Mapped[str | None] = mapped_column(String(100))
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    university_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("universities.id", ondelete="SET NULL"),
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scrape_interval_hours: Mapped[int] = mapped_column(Integer, default=168, nullable=False)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class IngestionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingestion_jobs"

    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    triggered_by: Mapped[str] = mapped_column(String(50), default="scheduler")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_sources: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    succeeded: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    duplicates_merged: Mapped[int] = mapped_column(Integer, default=0)
    embeddings_indexed: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    items: Mapped[list["IngestionJobItem"]] = relationship(
        "IngestionJobItem",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class IngestionJobItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingestion_job_items"

    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingestion_jobs.id", ondelete="CASCADE"),
        index=True,
    )
    source_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingestion_sources.id", ondelete="SET NULL"),
    )
    university_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("universities.id", ondelete="SET NULL"),
    )
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    stage: Mapped[str | None] = mapped_column(String(50))
    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    is_duplicate: Mapped[bool] = mapped_column(default=False)
    duplicate_of_id: Mapped[UUID | None] = mapped_column(ForeignKey("universities.id", ondelete="SET NULL"))
    error_message: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    normalized_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    validation_report: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    job: Mapped["IngestionJob"] = relationship("IngestionJob", back_populates="items")


class UniversityFingerprint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Deduplication index for universities at scale."""

    __tablename__ = "university_fingerprints"
    __table_args__ = (UniqueConstraint("fingerprint_hash", name="uq_university_fingerprints_hash"),)

    university_id: Mapped[UUID] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    fingerprint_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    website_domain: Mapped[str | None] = mapped_column(String(255), index=True)
    country: Mapped[str | None] = mapped_column(String(100), index=True)
