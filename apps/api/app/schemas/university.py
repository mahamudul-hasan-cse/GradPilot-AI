from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    university_id: UUID
    name: str
    degree_type: str
    field_of_study: str | None
    duration_months: int | None
    tuition_fee: Decimal | None
    tuition_currency: str | None
    language: str | None
    description: str | None
    requirements: dict[str, Any] | None
    application_deadline: date | None
    is_active: bool
    created_at: datetime


class UniversityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country: str
    city: str | None
    website: str | None
    ranking: int | None
    description: str | None
    logo_url: str | None
    tuition_fee: Decimal | None = None
    application_fee: Decimal | None = None
    minimum_gpa: Decimal | None = None
    minimum_ielts: Decimal | None = None
    minimum_toefl: int | None = None
    deadline: date | None = None
    programs: list[str] | None = None
    scholarships_available: bool = False
    majors: list[str] | None = None
    is_active: bool
    created_at: datetime


class UniversityDetailResponse(UniversityResponse):
    detailed_programs: list[ProgramResponse] = Field(default_factory=list)


class UniversitySearchParams(BaseModel):
    country: str | None = None
    query: str | None = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
