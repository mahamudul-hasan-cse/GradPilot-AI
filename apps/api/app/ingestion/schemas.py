"""Pydantic schemas for the ingestion pipeline."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class RawProgramData(BaseModel):
    name: str
    degree_type: str | None = None
    field_of_study: str | None = None
    tuition_fee: Decimal | None = None
    tuition_currency: str | None = "USD"
    duration_months: int | None = None
    application_deadline: date | None = None
    description: str | None = None
    requirements: dict[str, Any] | None = None


class RawScholarshipData(BaseModel):
    title: str
    provider: str | None = None
    amount: Decimal | None = None
    currency: str | None = "USD"
    description: str | None = None
    eligibility: str | None = None
    deadline: date | None = None
    application_url: str | None = None


class RawAdmissionRequirements(BaseModel):
    minimum_gpa: Decimal | None = None
    minimum_ielts: Decimal | None = None
    minimum_toefl: int | None = None
    notes: str | None = None


class ExtractedUniversityData(BaseModel):
    name: str
    country: str | None = None
    city: str | None = None
    website: str | None = None
    description: str | None = None
    ranking: int | None = None
    tuition_fee: Decimal | None = None
    application_fee: Decimal | None = None
    deadline: date | None = None
    programs: list[RawProgramData] = Field(default_factory=list)
    scholarships: list[RawScholarshipData] = Field(default_factory=list)
    admission_requirements: RawAdmissionRequirements | None = None
    scholarships_available: bool = False
    raw_html_length: int = 0
    extraction_method: str = "heuristic"


class NormalizedUniversityData(BaseModel):
    name: str
    country: str
    city: str | None = None
    website: str | None = None
    description: str | None = None
    ranking: int | None = None
    tuition_fee: Decimal | None = None
    application_fee: Decimal | None = None
    minimum_gpa: Decimal | None = None
    minimum_ielts: Decimal | None = None
    minimum_toefl: int | None = None
    deadline: date | None = None
    programs: list[str] = Field(default_factory=list)
    majors: list[str] = Field(default_factory=list)
    scholarships_available: bool = False
    program_records: list[RawProgramData] = Field(default_factory=list)
    scholarships: list[RawScholarshipData] = Field(default_factory=list)
    source_url: str
    external_id: str | None = None
    content_hash: str


class ValidationIssue(BaseModel):
    field: str
    severity: str  # error | warning
    message: str


class ValidationReport(BaseModel):
    score: float = Field(ge=0, le=100)
    passed: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    fields_present: int = 0
    fields_required: int = 0


class DedupResult(BaseModel):
    is_duplicate: bool = False
    duplicate_of_id: UUID | None = None
    match_type: str | None = None  # hash | domain | fuzzy
    confidence: float = 0.0


class ScrapeResult(BaseModel):
    url: str
    status_code: int
    html: str
    content_type: str | None = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    error: str | None = None
