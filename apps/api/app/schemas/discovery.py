from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.university import UniversityResponse


class UniversityFilterRequest(BaseModel):
    country: str | None = Field(default=None, description="Filter by country name")
    city: str | None = Field(default=None, description="Filter by city")
    major: str | None = Field(default=None, description="Filter by major or field of study")
    min_ranking: int | None = Field(default=None, ge=1, description="Minimum world ranking (lower is better)")
    max_ranking: int | None = Field(default=None, ge=1, description="Maximum world ranking")
    max_tuition: Decimal | None = Field(default=None, ge=0, description="Maximum annual tuition (USD)")
    min_tuition: Decimal | None = Field(default=None, ge=0)
    max_gpa_required: Decimal | None = Field(default=None, ge=0, le=4)
    min_gpa_required: Decimal | None = Field(default=None, ge=0, le=4)
    max_ielts_required: Decimal | None = Field(default=None, ge=0, le=9)
    scholarships_available: bool | None = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class UniversitySearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500, description="Keyword search query")
    country: str | None = None
    major: str | None = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class SemanticSearchRequest(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=1000,
        description="Natural language query, e.g. 'affordable CS masters in Canada'",
    )
    country: str | None = None
    major: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class RankingScoreBreakdown(BaseModel):
    gpa_match: float
    ielts_match: float
    budget_match: float
    ranking_preference: float
    scholarship_availability: float
    composite_score: float
    tier: str


class ScoredUniversityResponse(UniversityResponse):
    match_score: float
    ranking_breakdown: RankingScoreBreakdown
    semantic_score: float | None = None


class UniversitySearchResult(BaseModel):
    items: list[ScoredUniversityResponse]
    total: int
    skip: int
    limit: int
    search_mode: str


class RecommendUniversitiesRequest(BaseModel):
    cgpa: Decimal = Field(ge=0, le=4, description="Student CGPA on 4.0 scale")
    ielts: Decimal = Field(ge=0, le=9, description="IELTS overall band score")
    budget: Decimal = Field(ge=0, description="Annual budget in USD")
    country: str | None = Field(default=None, description="Preferred destination country")
    major: str = Field(min_length=1, max_length=255, description="Intended major or field of study")
    limit_per_tier: int = Field(default=5, ge=1, le=20)


class RecommendationTier(BaseModel):
    safe: list[ScoredUniversityResponse] = Field(default_factory=list)
    target: list[ScoredUniversityResponse] = Field(default_factory=list)
    ambitious: list[ScoredUniversityResponse] = Field(default_factory=list)


class RecommendUniversitiesResponse(BaseModel):
    input: RecommendUniversitiesRequest
    recommendations: RecommendationTier
    total_candidates_evaluated: int
