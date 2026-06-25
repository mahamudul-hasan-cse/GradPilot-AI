from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScholarshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    provider: str
    country: str | None
    amount: Decimal | None
    currency: str | None
    description: str | None
    eligibility: str | None
    deadline: date | None
    application_url: str | None
    degree_level: str | None = None
    funding_type: str | None = None
    minimum_gpa: Decimal | None = None
    minimum_ielts: Decimal | None = None
    research_required: bool = False
    work_experience_required_years: int | None = None
    eligible_nationalities: list[str] | None = None
    eligible_majors: list[str] | None = None
    is_active: bool
    created_at: datetime


class ScholarshipSearchParams(BaseModel):
    country: str | None = None
    query: str | None = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
