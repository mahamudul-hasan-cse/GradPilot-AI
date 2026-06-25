"""Recommendation scoring system — 0-100 scale."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from app.models.university import University

WEIGHTS = {
    "academic": 0.35,
    "language": 0.20,
    "budget": 0.20,
    "program": 0.15,
    "scholarship": 0.10,
}

TIER_SAFE_MIN = 80
TIER_TARGET_MIN = 60


@dataclass
class StudentRecommendationProfile:
    cgpa: Decimal
    ielts: Decimal
    budget: Decimal
    major: str
    country_preference: str | None = None
    work_experience_years: int = 0
    has_research_experience: bool = False


@dataclass
class ScoreBreakdown:
    academic_match: float
    language_match: float
    budget_match: float
    program_match: float
    scholarship_match: float
    recommendation_score: float
    tier: str


def _to_float(value: Decimal | float | int | None, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def score_academic_match(
    profile: StudentRecommendationProfile,
    university: University,
) -> float:
    student_gpa = _to_float(profile.cgpa)
    required_gpa = _to_float(university.minimum_gpa, default=3.0)

    if university.minimum_gpa is None:
        gpa_factor = 0.80
    elif student_gpa >= required_gpa:
        margin = student_gpa - required_gpa
        gpa_factor = min(1.0, 0.80 + margin * 0.25)
    else:
        gpa_factor = max(0.0, (student_gpa / required_gpa) * 0.55)

    experience_bonus = 0.0
    if profile.work_experience_years >= 2:
        experience_bonus += 0.15
    elif profile.work_experience_years >= 1:
        experience_bonus += 0.08
    if profile.has_research_experience:
        experience_bonus += 0.12

    return min(1.0, gpa_factor * 0.85 + min(experience_bonus, 0.25) * 0.15 + experience_bonus * 0.5)


def score_language_match(profile: StudentRecommendationProfile, university: University) -> float:
    student = _to_float(profile.ielts)
    if university.minimum_ielts is None:
        return 0.80
    required = _to_float(university.minimum_ielts)
    if student >= required:
        margin = student - required
        return min(1.0, 0.82 + margin * 0.30)
    return max(0.0, (student / required) * 0.50)


def score_budget_match(profile: StudentRecommendationProfile, university: University) -> float:
    budget = _to_float(profile.budget)
    if university.tuition_fee is None:
        return 0.75
    tuition = _to_float(university.tuition_fee)
    if tuition <= 0:
        return 1.0
    if budget >= tuition:
        surplus = min(1.0, (budget - tuition) / tuition)
        return min(1.0, 0.88 + surplus * 0.12)
    return max(0.0, (budget / tuition) * 0.85)


def score_program_match(profile: StudentRecommendationProfile, university: University) -> float:
    major_lower = profile.major.lower().strip()
    if not major_lower:
        return 0.5

    candidates: list[str] = []
    if university.majors:
        candidates.extend(university.majors)
    if university.programs:
        candidates.extend(university.programs)
    if university.search_text:
        candidates.append(university.search_text)

    if not candidates:
        return 0.45

    best = 0.0
    major_tokens = set(re.findall(r"[a-z0-9]+", major_lower))
    for item in candidates:
        item_lower = item.lower()
        if major_lower in item_lower or item_lower in major_lower:
            return 1.0
        item_tokens = set(re.findall(r"[a-z0-9]+", item_lower))
        if not item_tokens:
            continue
        overlap = len(major_tokens & item_tokens) / max(len(major_tokens), 1)
        best = max(best, overlap)

    return min(1.0, max(0.3, best))


def score_scholarship_match(university: University) -> float:
    return 1.0 if university.scholarships_available else 0.30


def compute_recommendation_score(
    *,
    academic_match: float,
    language_match: float,
    budget_match: float,
    program_match: float,
    scholarship_match: float,
) -> float:
    weighted = (
        academic_match * WEIGHTS["academic"]
        + language_match * WEIGHTS["language"]
        + budget_match * WEIGHTS["budget"]
        + program_match * WEIGHTS["program"]
        + scholarship_match * WEIGHTS["scholarship"]
    )
    return round(weighted * 100, 2)


def classify_tier(score: float) -> str:
    if score >= TIER_SAFE_MIN:
        return "safe"
    if score >= TIER_TARGET_MIN:
        return "target"
    return "ambitious"


def score_university(
    university: University,
    profile: StudentRecommendationProfile,
) -> ScoreBreakdown:
    academic = round(score_academic_match(profile, university), 4)
    language = round(score_language_match(profile, university), 4)
    budget = round(score_budget_match(profile, university), 4)
    program = round(score_program_match(profile, university), 4)
    scholarship = round(score_scholarship_match(university), 4)

    recommendation_score = compute_recommendation_score(
        academic_match=academic,
        language_match=language,
        budget_match=budget,
        program_match=program,
        scholarship_match=scholarship,
    )
    tier = classify_tier(recommendation_score)

    return ScoreBreakdown(
        academic_match=academic,
        language_match=language,
        budget_match=budget,
        program_match=program,
        scholarship_match=scholarship,
        recommendation_score=recommendation_score,
        tier=tier,
    )
