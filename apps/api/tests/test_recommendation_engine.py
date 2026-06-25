"""Tests for the University Recommendation Engine."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.recommendation.explainer import RecommendationExplainer
from app.services.recommendation.scoring import (
    WEIGHTS,
    StudentRecommendationProfile,
    classify_tier,
    compute_recommendation_score,
    score_academic_match,
    score_budget_match,
    score_language_match,
    score_program_match,
    score_scholarship_match,
    score_university,
)


def _university(**kwargs):
    defaults = {
        "name": "Test University",
        "country": "United States",
        "minimum_gpa": Decimal("3.0"),
        "minimum_ielts": Decimal("6.5"),
        "tuition_fee": Decimal("40000"),
        "ranking": 50,
        "scholarships_available": True,
        "majors": ["Computer Science"],
        "programs": ["MSc Computer Science"],
        "search_text": "Computer Science masters program",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _profile(**kwargs):
    defaults = {
        "cgpa": Decimal("3.5"),
        "ielts": Decimal("7.0"),
        "budget": Decimal("50000"),
        "major": "Computer Science",
        "country_preference": "United States",
        "work_experience_years": 0,
        "has_research_experience": False,
    }
    defaults.update(kwargs)
    return StudentRecommendationProfile(**defaults)


class TestScoringWeights:
    def test_weights_sum_to_one(self):
        assert sum(WEIGHTS.values()) == pytest.approx(1.0)

    def test_perfect_score_is_100(self):
        score = compute_recommendation_score(
            academic_match=1.0,
            language_match=1.0,
            budget_match=1.0,
            program_match=1.0,
            scholarship_match=1.0,
        )
        assert score == 100.0


class TestTierClassification:
    def test_safe_at_80(self):
        assert classify_tier(80) == "safe"
        assert classify_tier(95) == "safe"

    def test_target_60_to_79(self):
        assert classify_tier(60) == "target"
        assert classify_tier(79) == "target"

    def test_ambitious_below_60(self):
        assert classify_tier(59) == "ambitious"
        assert classify_tier(30) == "ambitious"


class TestAcademicMatch:
    def test_exceeds_gpa_requirement(self):
        uni = _university(minimum_gpa=Decimal("3.0"))
        profile = _profile(cgpa=Decimal("3.8"))
        assert score_academic_match(profile, uni) > 0.8

    def test_work_experience_boosts_score(self):
        uni = _university()
        without_exp = score_academic_match(_profile(work_experience_years=0), uni)
        with_exp = score_academic_match(_profile(work_experience_years=3), uni)
        assert with_exp > without_exp

    def test_research_experience_boosts_score(self):
        uni = _university()
        without = score_academic_match(_profile(has_research_experience=False), uni)
        with_research = score_academic_match(_profile(has_research_experience=True), uni)
        assert with_research > without


class TestProgramMatch:
    def test_exact_major_match(self):
        uni = _university(majors=["Computer Science"], programs=["MSc Computer Science"])
        score = score_program_match(_profile(major="Computer Science"), uni)
        assert score == 1.0

    def test_partial_major_match(self):
        uni = _university(majors=["Software Engineering"], programs=[])
        score = score_program_match(_profile(major="Software"), uni)
        assert score >= 0.3


class TestBudgetAndLanguage:
    def test_budget_within_range(self):
        assert score_budget_match(_profile(budget=Decimal("50000")), _university(tuition_fee=Decimal("40000"))) >= 0.85

    def test_ielts_meets_requirement(self):
        assert score_language_match(_profile(ielts=Decimal("7.0")), _university(minimum_ielts=Decimal("6.5"))) > 0.8


class TestScholarshipMatch:
    def test_scholarship_available_scores_higher(self):
        with_sch = score_scholarship_match(_university(scholarships_available=True))
        without = score_scholarship_match(_university(scholarships_available=False))
        assert with_sch > without


class TestScoreUniversity:
    def test_strong_profile_scores_safe(self):
        result = score_university(_university(), _profile())
        assert result.recommendation_score >= 60
        assert result.tier in {"safe", "target", "ambitious"}

    def test_weak_profile_lower_score(self):
        strong = score_university(_university(), _profile(cgpa=Decimal("3.8"), ielts=Decimal("7.5"), budget=Decimal("60000")))
        weak = score_university(
            _university(minimum_gpa=Decimal("3.8"), minimum_ielts=Decimal("7.5"), tuition_fee=Decimal("60000")),
            _profile(cgpa=Decimal("2.5"), ielts=Decimal("5.5"), budget=Decimal("20000")),
        )
        assert strong.recommendation_score > weak.recommendation_score


class TestExplainer:
    def test_generates_readable_explanation(self):
        uni = _university()
        profile = _profile()
        breakdown = score_university(uni, profile)
        explanation = RecommendationExplainer().explain(uni, profile, breakdown)

        assert "GPA" in explanation or "gpa" in explanation.lower()
        assert "IELTS" in explanation
        assert "budget" in explanation.lower() or "Tuition" in explanation
        assert "Scholarship" in explanation or "scholarship" in explanation.lower()
        assert breakdown.tier.capitalize() in explanation or breakdown.tier in explanation

    def test_explains_gpa_shortfall(self):
        uni = _university(minimum_gpa=Decimal("3.8"))
        profile = _profile(cgpa=Decimal("3.0"))
        breakdown = score_university(uni, profile)
        explanation = RecommendationExplainer().explain(uni, profile, breakdown)
        assert "below" in explanation.lower() or "GPA" in explanation


class TestRecommendationCache:
    def test_cache_key_is_deterministic(self):
        from app.services.recommendation.cache import RecommendationCache

        payload = {"cgpa": "3.5", "major": "CS", "ielts": "7.0"}
        cache = RecommendationCache()
        k1 = cache.build_cache_key(payload)
        k2 = cache.build_cache_key(payload)
        assert k1 == k2
        assert k1.startswith("rec:universities:")
