from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StudentProfileBase(BaseModel):
    nationality: str | None = None
    current_country: str | None = None
    education_level: str | None = None
    field_of_study: str | None = None
    gpa: Decimal | None = Field(default=None, ge=0, le=10)
    gpa_scale: Decimal | None = Field(default=Decimal("4.0"), ge=0, le=10)
    target_degree: str | None = None
    target_countries: list[str] | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    budget_currency: str | None = "USD"
    test_scores: dict[str, Any] | None = None
    work_experience_years: int | None = Field(default=None, ge=0)
    bio: str | None = None


class StudentProfileCreate(StudentProfileBase):
    pass


class StudentProfileUpdate(StudentProfileBase):
    pass


class StudentProfileResponse(StudentProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
