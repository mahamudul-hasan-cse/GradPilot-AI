"""Eligibility scoring for scholarship matching — 0-100 scale."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from app.models.scholarship import Scholarship

WEIGHTS = {
    "academic": 0.30,
    "language": 0.20,
    "degree": 0.15,
    "country": 0.15,
    "research": 0.10,
    "work_experience": 0.10,
}

DEGREE_ALIASES = {
    "bachelors": {"bachelor", "bachelors", "undergraduate", "bs", "ba", "bsc"},
    "masters": {"master", "masters", "msc", "ma", "ms", "mba", "graduate", "postgraduate"},
    "phd": {"phd", "doctorate", "doctoral", "doctor"},
}


@dataclass
class ScholarshipStudentProfile:
    cgpa: Decimal
    ielts: Decimal
    degree_level: str
    major: str
    country_preference: str | None = None
    has_research_experience: bool = False
    work_experience_years: int = 0
    nationality: str | None = None


@dataclass
class ScholarshipScoreBreakdown:
    academic_match: float
    language_match: float
    degree_match: float
    country_match: float
    research_match: float
    work_experience_match: float
    scholarship_score: float
    eligibility_probability: float
    match_category: str


def _to_float(value: Decimal | float | int | None, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _normalize_degree(level: str | None) -> str | None:
    if not level:
        return None
    token = level.lower().strip()
    for canonical, aliases in DEGREE_ALIASES.items():
        if token == canonical or token in aliases:
            return canonical
    return token


def score_academic_match(profile: ScholarshipStudentProfile, scholarship: Scholarship) -> float:
    student = _to_float(profile.cgpa)
    if scholarship.minimum_gpa is None:
        return 0.80
    required = _to_float(scholarship.minimum_gpa)
    if student >= required:
        margin = student - required
        return min(1.0, 0.82 + margin * 0.25)
    return max(0.0, (student / required) * 0.50)


def score_language_match(profile: ScholarshipStudentProfile, scholarship: Scholarship) -> float:
    student = _to_float(profile.ielts)
    if scholarship.minimum_ielts is None:
        return 0.80
    required = _to_float(scholarship.minimum_ielts)
    if student >= required:
        margin = student - required
        return min(1.0, 0.82 + margin * 0.30)
    return max(0.0, (student / required) * 0.50)


def score_degree_match(profile: ScholarshipStudentProfile, scholarship: Scholarship) -> float:
    student_degree = _normalize_degree(profile.degree_level)
    scholarship_degree = _normalize_degree(scholarship.degree_level)
    if scholarship_degree is None:
        return 0.75
    if student_degree is None:
        return 0.40
    if student_degree == scholarship_degree:
        return 1.0
    level_order = {"bachelors": 1, "masters": 2, "phd": 3}
    s_rank = level_order.get(student_degree, 2)
    sch_rank = level_order.get(scholarship_degree, 2)
    if s_rank >= sch_rank:
        return 0.65
    return 0.35


def score_country_match(profile: ScholarshipStudentProfile, scholarship: Scholarship) -> float:
    if not scholarship.country:
        return 0.70
    if not profile.country_preference:
        return 0.60
    pref = profile.country_preference.lower().strip()
    sch_country = scholarship.country.lower().strip()
    if pref in sch_country or sch_country in pref:
        return 1.0
    return 0.25


def score_research_match(profile: ScholarshipStudentProfile, scholarship: Scholarship) -> float:
    if not scholarship.research_required:
        return 1.0 if profile.has_research_experience else 0.85
    return 1.0 if profile.has_research_experience else 0.20


def score_work_experience_match(profile: ScholarshipStudentProfile, scholarship: Scholarship) -> float:
    required = scholarship.work_experience_required_years
    if required is None or required <= 0:
        return 0.85 if profile.work_experience_years > 0 else 0.75
    if profile.work_experience_years >= required:
        surplus = min(1.0, (profile.work_experience_years - required) / max(required, 1))
        return min(1.0, 0.85 + surplus * 0.15)
    return max(0.0, profile.work_experience_years / required * 0.55)


def score_nationality_eligibility(profile: ScholarshipStudentProfile, scholarship: Scholarship) -> float:
    """Gate factor — returns 0 if nationality explicitly excluded."""
    if not scholarship.eligible_nationalities or not profile.nationality:
        return 1.0
    nat = profile.nationality.lower().strip()
    eligible = [n.lower().strip() for n in scholarship.eligible_nationalities]
    if any(nat in e or e in nat for e in eligible):
        return 1.0
    return 0.0


def score_major_relevance(profile: ScholarshipStudentProfile, scholarship: Scholarship) -> float:
    if not scholarship.eligible_majors:
        return 1.0
    major_lower = profile.major.lower()
    for m in scholarship.eligible_majors:
        ml = m.lower()
        if major_lower in ml or ml in major_lower:
            return 1.0
    major_tokens = set(re.findall(r"[a-z0-9]+", major_lower))
    for m in scholarship.eligible_majors:
        if major_tokens & set(re.findall(r"[a-z0-9]+", m.lower())):
            return 0.7
    return 0.4


def compute_scholarship_score(
    *,
    academic_match: float,
    language_match: float,
    degree_match: float,
    country_match: float,
    research_match: float,
    work_experience_match: float,
    nationality_gate: float = 1.0,
    major_factor: float = 1.0,
) -> float:
    weighted = (
        academic_match * WEIGHTS["academic"]
        + language_match * WEIGHTS["language"]
        + degree_match * WEIGHTS["degree"]
        + country_match * WEIGHTS["country"]
        + research_match * WEIGHTS["research"]
        + work_experience_match * WEIGHTS["work_experience"]
    )
    raw = weighted * 100 * nationality_gate
    adjusted = raw * (0.85 + 0.15 * major_factor)
    return round(min(100.0, max(0.0, adjusted)), 2)


def compute_eligibility_probability(scholarship_score: float) -> float:
    """Map scholarship score to eligibility probability (0-1)."""
    if scholarship_score >= 90:
        base = 0.88 + (scholarship_score - 90) * 0.008
    elif scholarship_score >= 75:
        base = 0.72 + (scholarship_score - 75) * 0.0107
    elif scholarship_score >= 60:
        base = 0.50 + (scholarship_score - 60) * 0.0147
    else:
        base = scholarship_score / 100 * 0.50
    return round(min(0.98, max(0.05, base)), 4)


def classify_match_category(score: float) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "strong"
    if score >= 60:
        return "possible"
    return "low"


class EligibilityScoringEngine:
    def score(
        self,
        scholarship: Scholarship,
        profile: ScholarshipStudentProfile,
    ) -> ScholarshipScoreBreakdown:
        nationality_gate = score_nationality_eligibility(profile, scholarship)
        major_factor = score_major_relevance(profile, scholarship)

        academic = round(score_academic_match(profile, scholarship), 4)
        language = round(score_language_match(profile, scholarship), 4)
        degree = round(score_degree_match(profile, scholarship), 4)
        country = round(score_country_match(profile, scholarship), 4)
        research = round(score_research_match(profile, scholarship), 4)
        work = round(score_work_experience_match(profile, scholarship), 4)

        scholarship_score = compute_scholarship_score(
            academic_match=academic,
            language_match=language,
            degree_match=degree,
            country_match=country,
            research_match=research,
            work_experience_match=work,
            nationality_gate=nationality_gate,
            major_factor=major_factor,
        )
        eligibility_probability = compute_eligibility_probability(scholarship_score)
        match_category = classify_match_category(scholarship_score)

        return ScholarshipScoreBreakdown(
            academic_match=academic,
            language_match=language,
            degree_match=degree,
            country_match=country,
            research_match=research,
            work_experience_match=work,
            scholarship_score=scholarship_score,
            eligibility_probability=eligibility_probability,
            match_category=match_category,
        )

    def score_batch(
        self,
        scholarships: list[Scholarship],
        profile: ScholarshipStudentProfile,
    ) -> list[tuple[Scholarship, ScholarshipScoreBreakdown]]:
        return [(s, self.score(s, profile)) for s in scholarships]
