"""API schemas for ingestion monitoring."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IngestionSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    source_url: str = Field(min_length=1, max_length=1000)
    country: str | None = None
    city: str | None = None
    external_id: str | None = None
    priority: int = Field(default=100, ge=1, le=1000)
    scrape_interval_hours: int = Field(default=168, ge=1)


class IngestionSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_url: str
    country: str | None
    city: str | None
    is_active: bool
    priority: int
    last_scraped_at: datetime | None
    last_success_at: datetime | None
    consecutive_failures: int
    university_id: UUID | None


class IngestionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_type: str
    status: str
    triggered_by: str
    total_sources: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    duplicates_merged: int
    embeddings_indexed: int
    started_at: datetime | None
    completed_at: datetime | None
    metrics: dict[str, Any] | None


class IngestionDashboardResponse(BaseModel):
    total_sources: int
    active_sources: int
    total_universities: int
    avg_quality_score: float
    failed_sources: int
    recent_jobs: list[dict[str, Any]]


class TriggerJobRequest(BaseModel):
    job_type: str = Field(default="incremental", pattern="^(incremental|full)$")
    batch_size: int | None = Field(default=None, ge=1, le=500)
