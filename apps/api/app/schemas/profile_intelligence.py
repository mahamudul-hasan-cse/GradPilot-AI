from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileAnalysisRequest(BaseModel):
    cgpa: Decimal = Field(ge=0, le=4, description="CGPA on a 4.0 scale")
    ielts: Decimal = Field(ge=0, le=9, description="IELTS overall band score")
    degree_level: str = Field(
        min_length=1,
        max_length=50,
        description="Target degree level: bachelors, masters, or phd",
    )
    major: str = Field(min_length=1, max_length=255)
    country_preferences: list[str] = Field(
        default_factory=list,
        description="Preferred study-abroad countries",
    )
    work_experience_years: int = Field(default=0, ge=0, le=50)
    has_research_experience: bool = Field(default=False)
    publications_count: int = Field(default=0, ge=0, le=500)
    certifications: list[str] = Field(default_factory=list)
    target_intake: str | None = Field(
        default=None,
        max_length=50,
        description="Target intake term, e.g. Fall 2026",
    )
    use_cache: bool = Field(default=True)
    analyzer_type: str = Field(
        default="rule_based",
        description="Analyzer to use: rule_based (default) or ml (future)",
    )


class ScoreExplanation(BaseModel):
    score: float
    label: str
    explanation: str
    factors: dict[str, float] = Field(default_factory=dict)


class ProfileAnalysisResponse(BaseModel):
    admission_readiness_score: float = Field(description="Overall admission readiness 0-100")
    scholarship_readiness_score: float = Field(description="Scholarship competitiveness 0-100")
    employability_score: float = Field(description="Post-graduation employability 0-100")
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    recommended_countries: list[str] = Field(default_factory=list)
    recommended_university_tier: str = Field(
        description="Suggested university tier based on profile strength",
    )
    profile_summary: str = Field(description="Human-readable executive summary")
    score_explanations: dict[str, ScoreExplanation] = Field(
        default_factory=dict,
        description="Detailed explanation for each score",
    )
    analyzer_type: str = "rule_based"
    cache_hit: bool = False
    history_id: UUID | None = None


class ProfileAnalysisAnalytics(BaseModel):
    total_analyses: int
    avg_admission_readiness_score: float
    avg_scholarship_readiness_score: float
    avg_employability_score: float
    cache_hit_rate: float
    tier_distribution: dict[str, int]
    analyzer_distribution: dict[str, int]
    recent_analyses: list[dict[str, Any]] = Field(default_factory=list)
