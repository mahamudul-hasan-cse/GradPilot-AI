"""Base types and analyzer protocol for profile intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol


@dataclass
class StudentAnalysisProfile:
    cgpa: Decimal
    ielts: Decimal
    degree_level: str
    major: str
    country_preferences: list[str] = field(default_factory=list)
    work_experience_years: int = 0
    has_research_experience: bool = False
    publications_count: int = 0
    certifications: list[str] = field(default_factory=list)
    target_intake: str | None = None


@dataclass
class ProfileAnalysisResult:
    admission_readiness_score: float
    scholarship_readiness_score: float
    employability_score: float
    strengths: list[str]
    weaknesses: list[str]
    missing_requirements: list[str]
    recommended_actions: list[str]
    recommended_countries: list[str]
    recommended_university_tier: str
    profile_summary: str
    score_explanations: dict[str, dict]
    analyzer_type: str = "rule_based"


class ProfileAnalyzer(Protocol):
    """Pluggable analyzer interface — supports rule-based and future ML backends."""

    analyzer_type: str

    def analyze(self, profile: StudentAnalysisProfile) -> ProfileAnalysisResult: ...
