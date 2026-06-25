from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.scholarship import ScholarshipResponse


class ScholarshipRecommendationRequest(BaseModel):
    cgpa: Decimal = Field(ge=0, le=4, description="Student CGPA on 4.0 scale")
    ielts: Decimal = Field(ge=0, le=9, description="IELTS overall band score")
    degree_level: str = Field(
        min_length=1,
        max_length=50,
        description="Target degree level: bachelors, masters, or phd",
    )
    major: str = Field(min_length=1, max_length=255)
    country_preference: str | None = Field(default=None, description="Preferred scholarship country")
    has_research_experience: bool = Field(default=False)
    work_experience_years: int = Field(default=0, ge=0, le=50)
    nationality: str | None = Field(default=None, description="Student nationality for eligibility checks")
    min_score: float = Field(default=0, ge=0, le=100, description="Minimum scholarship score to include")
    limit: int = Field(default=50, ge=1, le=200, description="Max scholarships to return")
    use_cache: bool = Field(default=True)


class ScholarshipScoreDetail(BaseModel):
    academic_match: float
    language_match: float
    degree_match: float
    country_match: float
    research_match: float
    work_experience_match: float
    scholarship_score: float = Field(description="Weighted score 0-100")
    eligibility_probability: float = Field(description="Estimated eligibility probability 0-1")
    match_category: str = Field(description="excellent | strong | possible | low")


class MatchedScholarship(BaseModel):
    scholarship: ScholarshipResponse
    score: ScholarshipScoreDetail
    explanation: str


class ScholarshipMatchGroups(BaseModel):
    excellent: list[MatchedScholarship] = Field(default_factory=list)
    strong: list[MatchedScholarship] = Field(default_factory=list)
    possible: list[MatchedScholarship] = Field(default_factory=list)
    low: list[MatchedScholarship] = Field(default_factory=list)


class ScholarshipRecommendationResponse(BaseModel):
    request: ScholarshipRecommendationRequest
    matches: list[MatchedScholarship]
    grouped: ScholarshipMatchGroups
    total_candidates_evaluated: int
    cache_hit: bool = False
    history_id: UUID | None = None
    scoring_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "academic_match": 0.30,
            "language_match": 0.20,
            "degree_match": 0.15,
            "country_match": 0.15,
            "research_match": 0.10,
            "work_experience_match": 0.10,
        }
    )


class ScholarshipRecommendationAnalytics(BaseModel):
    total_recommendations: int
    avg_scholarship_score: float
    avg_eligibility_probability: float
    cache_hit_rate: float
    match_distribution: dict[str, int]
    total_active_scholarships: int
    recent_requests: list[dict[str, Any]] = Field(default_factory=list)
