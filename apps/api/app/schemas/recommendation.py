from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.university import UniversityResponse


class UniversityRecommendationRequest(BaseModel):
    cgpa: Decimal = Field(ge=0, le=4, description="Student CGPA on 4.0 scale")
    ielts: Decimal = Field(ge=0, le=9, description="IELTS overall band score")
    budget: Decimal = Field(ge=0, description="Annual budget in USD")
    country_preference: str | None = Field(default=None, description="Preferred destination country")
    major: str = Field(min_length=1, max_length=255, description="Intended major or field of study")
    work_experience_years: int = Field(default=0, ge=0, le=50)
    has_research_experience: bool = Field(default=False)
    limit_per_tier: int = Field(default=10, ge=1, le=50)
    use_cache: bool = Field(default=True, description="Return cached result if available")


class RecommendationScoreBreakdown(BaseModel):
    academic_match: float = Field(description="Academic match factor (0-1)")
    language_match: float = Field(description="Language/IELTS match factor (0-1)")
    budget_match: float = Field(description="Budget match factor (0-1)")
    program_match: float = Field(description="Program/major match factor (0-1)")
    scholarship_match: float = Field(description="Scholarship availability factor (0-1)")
    recommendation_score: float = Field(description="Weighted score 0-100")
    tier: str = Field(description="safe | target | ambitious")


class RecommendedUniversity(BaseModel):
    university: UniversityResponse
    score_breakdown: RecommendationScoreBreakdown
    explanation: str


class RecommendationTierGroup(BaseModel):
    safe: list[RecommendedUniversity] = Field(default_factory=list)
    target: list[RecommendedUniversity] = Field(default_factory=list)
    ambitious: list[RecommendedUniversity] = Field(default_factory=list)


class UniversityRecommendationResponse(BaseModel):
    request: UniversityRecommendationRequest
    recommendations: RecommendationTierGroup
    total_candidates_evaluated: int
    cache_hit: bool = False
    history_id: UUID | None = None
    scoring_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "academic_match": 0.35,
            "language_match": 0.20,
            "budget_match": 0.20,
            "program_match": 0.15,
            "scholarship_match": 0.10,
        }
    )
