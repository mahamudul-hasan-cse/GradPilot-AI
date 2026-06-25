"""University match scoring and tier classification."""

from dataclasses import dataclass
from decimal import Decimal

from app.models.university import University

WEIGHTS = {
    "gpa": 0.25,
    "ielts": 0.20,
    "budget": 0.25,
    "ranking": 0.20,
    "scholarship": 0.10,
}


@dataclass
class StudentProfile:
    cgpa: Decimal
    ielts: Decimal
    budget: Decimal


@dataclass
class RankingBreakdown:
    gpa_match: float
    ielts_match: float
    budget_match: float
    ranking_preference: float
    scholarship_availability: float
    composite_score: float
    tier: str


def _to_float(value: Decimal | float | int | None, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def score_gpa_match(student_gpa: Decimal, minimum_gpa: Decimal | None) -> float:
    student = _to_float(student_gpa)
    if minimum_gpa is None:
        return 0.75
    required = _to_float(minimum_gpa)
    if required <= 0:
        return 0.75
    if student < required:
        return max(0.0, (student / required) * 0.45)
    margin = student - required
    return min(1.0, 0.72 + margin * 0.2)


def score_ielts_match(student_ielts: Decimal, minimum_ielts: Decimal | None) -> float:
    student = _to_float(student_ielts)
    if minimum_ielts is None:
        return 0.75
    required = _to_float(minimum_ielts)
    if student < required:
        return max(0.0, (student / required) * 0.45)
    margin = student - required
    return min(1.0, 0.72 + margin * 0.25)


def score_budget_match(budget: Decimal, tuition_fee: Decimal | None) -> float:
    budget_f = _to_float(budget)
    if tuition_fee is None:
        return 0.8
    tuition = _to_float(tuition_fee)
    if tuition <= 0:
        return 1.0
    if budget_f >= tuition:
        surplus_ratio = min(1.0, (budget_f - tuition) / tuition)
        return min(1.0, 0.85 + surplus_ratio * 0.15)
    return max(0.0, budget_f / tuition)


def score_ranking_preference(ranking: int | None) -> float:
    if ranking is None:
        return 0.5
    if ranking <= 10:
        return 1.0
    if ranking <= 50:
        return 0.85
    if ranking <= 100:
        return 0.7
    if ranking <= 200:
        return 0.55
    return max(0.25, 1.0 - (ranking / 500))


def score_scholarship_availability(scholarships_available: bool) -> float:
    return 1.0 if scholarships_available else 0.35


def compute_composite_score(
    *,
    gpa_match: float,
    ielts_match: float,
    budget_match: float,
    ranking_preference: float,
    scholarship_availability: float,
) -> float:
    return (
        gpa_match * WEIGHTS["gpa"]
        + ielts_match * WEIGHTS["ielts"]
        + budget_match * WEIGHTS["budget"]
        + ranking_preference * WEIGHTS["ranking"]
        + scholarship_availability * WEIGHTS["scholarship"]
    )


def classify_tier(
    *,
    composite_score: float,
    gpa_match: float,
    ielts_match: float,
    budget_match: float,
    ranking: int | None,
) -> str:
    fit_score = min(gpa_match, ielts_match, budget_match)
    is_prestigious = ranking is not None and ranking <= 50

    if fit_score >= 0.82 and composite_score >= 0.68:
        return "safe"
    if is_prestigious and (fit_score < 0.65 or composite_score < 0.58):
        return "ambitious"
    if composite_score < 0.45 or fit_score < 0.4:
        return "ambitious"
    if fit_score >= 0.6 and composite_score >= 0.52:
        return "target"
    return "target" if composite_score >= 0.48 else "ambitious"


def rank_university(university: University, profile: StudentProfile) -> RankingBreakdown:
    gpa_match = score_gpa_match(profile.cgpa, university.minimum_gpa)
    ielts_match = score_ielts_match(profile.ielts, university.minimum_ielts)
    budget_match = score_budget_match(profile.budget, university.tuition_fee)
    ranking_preference = score_ranking_preference(university.ranking)
    scholarship_availability = score_scholarship_availability(university.scholarships_available)

    composite = compute_composite_score(
        gpa_match=gpa_match,
        ielts_match=ielts_match,
        budget_match=budget_match,
        ranking_preference=ranking_preference,
        scholarship_availability=scholarship_availability,
    )
    tier = classify_tier(
        composite_score=composite,
        gpa_match=gpa_match,
        ielts_match=ielts_match,
        budget_match=budget_match,
        ranking=university.ranking,
    )

    return RankingBreakdown(
        gpa_match=round(gpa_match, 4),
        ielts_match=round(ielts_match, 4),
        budget_match=round(budget_match, 4),
        ranking_preference=round(ranking_preference, 4),
        scholarship_availability=round(scholarship_availability, 4),
        composite_score=round(composite, 4),
        tier=tier,
    )
