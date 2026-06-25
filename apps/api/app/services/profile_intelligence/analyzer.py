"""Rule-based profile analyzer — scores, strengths, weaknesses, and gaps."""

from __future__ import annotations

from decimal import Decimal

from app.services.profile_intelligence.base import (
    ProfileAnalysisResult,
    StudentAnalysisProfile,
)
from app.services.profile_intelligence.recommendations import RecommendationGenerator

ADMISSION_WEIGHTS = {
    "academic": 0.30,
    "language": 0.25,
    "research": 0.20,
    "work": 0.10,
    "completeness": 0.15,
}

SCHOLARSHIP_WEIGHTS = {
    "academic": 0.30,
    "language": 0.20,
    "research": 0.25,
    "work": 0.15,
    "certifications": 0.10,
}

EMPLOYABILITY_WEIGHTS = {
    "work": 0.35,
    "certifications": 0.20,
    "research": 0.25,
    "academic": 0.20,
}

DEGREE_IELTS_BENCHMARKS = {
    "bachelors": Decimal("6.0"),
    "masters": Decimal("6.5"),
    "phd": Decimal("7.0"),
}

DEGREE_GPA_BENCHMARKS = {
    "bachelors": Decimal("3.0"),
    "masters": Decimal("3.2"),
    "phd": Decimal("3.5"),
}


def _to_float(value: Decimal | float | int) -> float:
    return float(value)


def _normalize_degree(level: str) -> str:
    token = level.lower().strip()
    if token in {"bachelor", "bachelors", "undergraduate", "bs", "ba"}:
        return "bachelors"
    if token in {"master", "masters", "msc", "ma", "ms", "mba", "graduate"}:
        return "masters"
    if token in {"phd", "doctorate", "doctoral"}:
        return "phd"
    return token


def score_academic(cgpa: Decimal, degree_level: str) -> float:
    gpa = _to_float(cgpa)
    benchmark = _to_float(DEGREE_GPA_BENCHMARKS.get(_normalize_degree(degree_level), Decimal("3.0")))
    if gpa >= benchmark + 0.4:
        return 1.0
    if gpa >= benchmark:
        return 0.82 + (gpa - benchmark) * 0.45
    return max(0.2, (gpa / benchmark) * 0.65)


def score_language(ielts: Decimal, degree_level: str) -> float:
    band = _to_float(ielts)
    benchmark = _to_float(DEGREE_IELTS_BENCHMARKS.get(_normalize_degree(degree_level), Decimal("6.5")))
    if band >= benchmark + 1.0:
        return 1.0
    if band >= benchmark:
        return 0.80 + (band - benchmark) * 0.20
    return max(0.15, (band / benchmark) * 0.60)


def score_research(profile: StudentAnalysisProfile) -> float:
    base = 0.35
    if profile.has_research_experience:
        base += 0.35
    if profile.publications_count >= 3:
        base += 0.30
    elif profile.publications_count >= 1:
        base += 0.20
    return min(1.0, base)


def score_work(years: int, degree_level: str) -> float:
    degree = _normalize_degree(degree_level)
    if years <= 0:
        return 0.45 if degree == "bachelors" else 0.35
    if years >= 5:
        return 1.0
    if years >= 3:
        return 0.85
    if years >= 1:
        return 0.70
    return 0.55


def score_certifications(certifications: list[str]) -> float:
    count = len(certifications)
    if count >= 4:
        return 1.0
    if count >= 2:
        return 0.80
    if count == 1:
        return 0.60
    return 0.30


def score_completeness(profile: StudentAnalysisProfile) -> float:
    score = 0.0
    if profile.country_preferences:
        score += 0.35
    if profile.target_intake:
        score += 0.30
    if profile.certifications:
        score += 0.20
    if profile.major:
        score += 0.15
    return min(1.0, score)


def weighted_score(components: dict[str, float], weights: dict[str, float]) -> float:
    total = sum(components[k] * weights[k] for k in weights)
    return round(min(100.0, max(0.0, total * 100)), 2)


def classify_university_tier(admission_score: float) -> str:
    if admission_score >= 85:
        return "Top Tier (R1 / Russell Group)"
    if admission_score >= 70:
        return "Competitive (Top 100)"
    if admission_score >= 55:
        return "Target (Mid-tier)"
    return "Foundation / Safety"


def detect_strengths(profile: StudentAnalysisProfile, components: dict[str, float]) -> list[str]:
    strengths: list[str] = []
    if components["academic"] >= 0.85:
        strengths.append(f"Strong academic record (CGPA {profile.cgpa})")
    if components["language"] >= 0.85:
        strengths.append(f"Excellent English proficiency (IELTS {profile.ielts})")
    if profile.has_research_experience:
        strengths.append("Research experience strengthens graduate applications")
    if profile.publications_count > 0:
        strengths.append(f"{profile.publications_count} publication(s) demonstrate research output")
    if profile.work_experience_years >= 2:
        strengths.append(f"{profile.work_experience_years} years of professional experience")
    if len(profile.certifications) >= 2:
        strengths.append(f"{len(profile.certifications)} relevant certifications")
    if profile.country_preferences:
        strengths.append("Clear country preferences help target applications")
    return strengths[:6]


def detect_weaknesses(profile: StudentAnalysisProfile, components: dict[str, float]) -> list[str]:
    weaknesses: list[str] = []
    degree = _normalize_degree(profile.degree_level)
    if components["academic"] < 0.65:
        weaknesses.append(f"CGPA ({profile.cgpa}) is below competitive benchmarks for {degree} programs")
    if components["language"] < 0.65:
        weaknesses.append(f"IELTS ({profile.ielts}) may limit options at top universities")
    if not profile.has_research_experience and degree in {"masters", "phd"}:
        weaknesses.append("No research experience — common gap for graduate programs")
    if profile.publications_count == 0 and degree == "phd":
        weaknesses.append("No publications — PhD applicants typically need research output")
    if profile.work_experience_years == 0 and degree == "masters":
        weaknesses.append("Limited work experience may reduce MBA and professional program options")
    if not profile.country_preferences:
        weaknesses.append("No country preferences — narrows strategic planning")
    if not profile.target_intake:
        weaknesses.append("No target intake set — timeline planning is unclear")
    return weaknesses[:6]


def detect_missing_requirements(profile: StudentAnalysisProfile) -> list[str]:
    missing: list[str] = []
    degree = _normalize_degree(profile.degree_level)
    benchmark_ielts = DEGREE_IELTS_BENCHMARKS.get(degree, Decimal("6.5"))
    benchmark_gpa = DEGREE_GPA_BENCHMARKS.get(degree, Decimal("3.0"))

    if profile.ielts < benchmark_ielts:
        missing.append(f"IELTS {benchmark_ielts}+ recommended for {degree} programs")
    if profile.cgpa < benchmark_gpa:
        missing.append(f"CGPA {benchmark_gpa}+ typically required for competitive {degree} admissions")
    if degree in {"masters", "phd"} and not profile.has_research_experience:
        missing.append("Research experience or thesis project")
    if degree == "phd" and profile.publications_count == 0:
        missing.append("At least one research publication or preprint")
    if not profile.target_intake:
        missing.append("Target intake term (e.g. Fall 2026)")
    if not profile.country_preferences:
        missing.append("At least one target country preference")
    if len(profile.certifications) == 0 and profile.work_experience_years > 0:
        missing.append("Professional certifications to validate industry skills")
    return missing[:8]


class RuleBasedProfileAnalyzer:
    analyzer_type = "rule_based"

    def __init__(self) -> None:
        self.recommendation_generator = RecommendationGenerator()

    def analyze(self, profile: StudentAnalysisProfile) -> ProfileAnalysisResult:
        academic = score_academic(profile.cgpa, profile.degree_level)
        language = score_language(profile.ielts, profile.degree_level)
        research = score_research(profile)
        work = score_work(profile.work_experience_years, profile.degree_level)
        completeness = score_completeness(profile)
        certifications = score_certifications(profile.certifications)

        admission_components = {
            "academic": academic,
            "language": language,
            "research": research,
            "work": work,
            "completeness": completeness,
        }
        scholarship_components = {
            "academic": academic,
            "language": language,
            "research": research,
            "work": work,
            "certifications": certifications,
        }
        employability_components = {
            "work": work,
            "certifications": certifications,
            "research": research,
            "academic": academic,
        }

        admission_score = weighted_score(admission_components, ADMISSION_WEIGHTS)
        scholarship_score = weighted_score(scholarship_components, SCHOLARSHIP_WEIGHTS)
        employability_score = weighted_score(employability_components, EMPLOYABILITY_WEIGHTS)

        tier = classify_university_tier(admission_score)
        strengths = detect_strengths(profile, admission_components)
        weaknesses = detect_weaknesses(profile, admission_components)
        missing = detect_missing_requirements(profile)

        recommendations = self.recommendation_generator.generate(
            profile=profile,
            admission_score=admission_score,
            scholarship_score=scholarship_score,
            weaknesses=weaknesses,
            missing=missing,
            components=admission_components,
        )

        score_explanations = self._build_explanations(
            profile=profile,
            admission_score=admission_score,
            scholarship_score=scholarship_score,
            employability_score=employability_score,
            admission_components=admission_components,
            scholarship_components=scholarship_components,
            employability_components=employability_components,
        )

        profile_summary = self._build_summary(
            profile=profile,
            admission_score=admission_score,
            scholarship_score=scholarship_score,
            employability_score=employability_score,
            tier=tier,
            strengths=strengths,
            weaknesses=weaknesses,
        )

        return ProfileAnalysisResult(
            admission_readiness_score=admission_score,
            scholarship_readiness_score=scholarship_score,
            employability_score=employability_score,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_requirements=missing,
            recommended_actions=recommendations["actions"],
            recommended_countries=recommendations["countries"],
            recommended_university_tier=tier,
            profile_summary=profile_summary,
            score_explanations=score_explanations,
            analyzer_type=self.analyzer_type,
        )

    def _build_explanations(
        self,
        *,
        profile: StudentAnalysisProfile,
        admission_score: float,
        scholarship_score: float,
        employability_score: float,
        admission_components: dict[str, float],
        scholarship_components: dict[str, float],
        employability_components: dict[str, float],
    ) -> dict[str, dict]:
        degree = _normalize_degree(profile.degree_level)
        return {
            "admission_readiness": {
                "score": admission_score,
                "label": "Admission Readiness",
                "explanation": (
                    f"Based on your {degree} profile, academic ({admission_components['academic']:.0%}), "
                    f"language ({admission_components['language']:.0%}), research ({admission_components['research']:.0%}), "
                    f"work ({admission_components['work']:.0%}), and profile completeness "
                    f"({admission_components['completeness']:.0%})."
                ),
                "factors": admission_components,
            },
            "scholarship_readiness": {
                "score": scholarship_score,
                "label": "Scholarship Readiness",
                "explanation": (
                    f"Scholarship competitiveness reflects academic strength, IELTS, research output, "
                    f"work experience, and certifications. Research component at "
                    f"{scholarship_components['research']:.0%} is key for merit-based funding."
                ),
                "factors": scholarship_components,
            },
            "employability": {
                "score": employability_score,
                "label": "Employability",
                "explanation": (
                    f"Post-graduation employability weighs work experience ({employability_components['work']:.0%}), "
                    f"certifications ({employability_components['certifications']:.0%}), research "
                    f"({employability_components['research']:.0%}), and academics "
                    f"({employability_components['academic']:.0%})."
                ),
                "factors": employability_components,
            },
        }

    def _build_summary(
        self,
        *,
        profile: StudentAnalysisProfile,
        admission_score: float,
        scholarship_score: float,
        employability_score: float,
        tier: str,
        strengths: list[str],
        weaknesses: list[str],
    ) -> str:
        degree = _normalize_degree(profile.degree_level)
        strength_note = strengths[0] if strengths else "building foundational credentials"
        weakness_note = weaknesses[0] if weaknesses else "no critical gaps identified"
        return (
            f"You are pursuing a {degree} in {profile.major} with admission readiness of "
            f"{admission_score:.0f}/100. Your profile suggests a {tier} targeting strategy. "
            f"Key strength: {strength_note.rstrip('.')}. "
            f"Priority gap: {weakness_note.rstrip('.')}. "
            f"Scholarship readiness is {scholarship_score:.0f}/100 and employability is "
            f"{employability_score:.0f}/100."
        )
