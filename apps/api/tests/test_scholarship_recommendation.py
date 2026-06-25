"""Tests for the Scholarship Matching Engine."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.recommendation.cache import RecommendationCache
from app.services.scholarship_recommendation.explainer import ScholarshipExplanationEngine
from app.services.scholarship_recommendation.scoring import (
    WEIGHTS,
    EligibilityScoringEngine,
    ScholarshipStudentProfile,
    classify_match_category,
    compute_eligibility_probability,
    compute_scholarship_score,
    score_academic_match,
    score_degree_match,
    score_nationality_eligibility,
    score_research_match,
)


def _scholarship(**kwargs):
    defaults = {
        "title": "Global Excellence Scholarship",
        "provider": "Test Foundation",
        "country": "United States",
        "degree_level": "masters",
        "funding_type": "full",
        "minimum_gpa": Decimal("3.2"),
        "minimum_ielts": Decimal("6.5"),
        "research_required": False,
        "work_experience_required_years": None,
        "eligible_nationalities": None,
        "eligible_majors": ["Computer Science"],
        "is_active": True,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _profile(**kwargs):
    defaults = {
        "cgpa": Decimal("3.6"),
        "ielts": Decimal("7.0"),
        "degree_level": "masters",
        "major": "Computer Science",
        "country_preference": "United States",
        "has_research_experience": False,
        "work_experience_years": 1,
        "nationality": "India",
    }
    defaults.update(kwargs)
    return ScholarshipStudentProfile(**defaults)


class TestWeights:
    def test_weights_sum_to_one(self):
        assert sum(WEIGHTS.values()) == pytest.approx(1.0)


class TestMatchCategories:
    def test_excellent(self):
        assert classify_match_category(90) == "excellent"
        assert classify_match_category(100) == "excellent"

    def test_strong(self):
        assert classify_match_category(75) == "strong"
        assert classify_match_category(89) == "strong"

    def test_possible(self):
        assert classify_match_category(60) == "possible"

    def test_low(self):
        assert classify_match_category(59) == "low"


class TestScoringFunctions:
    def test_academic_meets_requirement(self):
        assert score_academic_match(_profile(), _scholarship()) > 0.8

    def test_degree_match(self):
        assert score_degree_match(_profile(degree_level="masters"), _scholarship(degree_level="masters")) == 1.0

    def test_research_required_without_experience(self):
        assert score_research_match(
            _profile(has_research_experience=False),
            _scholarship(research_required=True),
        ) < 0.5

    def test_research_required_with_experience(self):
        assert score_research_match(
            _profile(has_research_experience=True),
            _scholarship(research_required=True),
        ) == 1.0

    def test_nationality_eligible(self):
        assert score_nationality_eligibility(
            _profile(nationality="India"),
            _scholarship(eligible_nationalities=["India", "Nigeria"]),
        ) == 1.0

    def test_nationality_ineligible(self):
        assert score_nationality_eligibility(
            _profile(nationality="Brazil"),
            _scholarship(eligible_nationalities=["India", "Nigeria"]),
        ) == 0.0


class TestCompositeScore:
    def test_perfect_score_near_100(self):
        score = compute_scholarship_score(
            academic_match=1.0,
            language_match=1.0,
            degree_match=1.0,
            country_match=1.0,
            research_match=1.0,
            work_experience_match=1.0,
        )
        assert score == 100.0

    def test_nationality_gate_zeros_score(self):
        score = compute_scholarship_score(
            academic_match=1.0,
            language_match=1.0,
            degree_match=1.0,
            country_match=1.0,
            research_match=1.0,
            work_experience_match=1.0,
            nationality_gate=0.0,
        )
        assert score == 0.0


class TestEligibilityProbability:
    def test_high_score_high_probability(self):
        assert compute_eligibility_probability(95) >= 0.85

    def test_low_score_low_probability(self):
        assert compute_eligibility_probability(30) < 0.30


class TestEligibilityScoringEngine:
    def test_strong_profile_high_score(self):
        engine = EligibilityScoringEngine()
        result = engine.score(_scholarship(), _profile())
        assert result.scholarship_score >= 60
        assert 0 < result.eligibility_probability <= 1
        assert result.match_category in {"excellent", "strong", "possible", "low"}

    def test_weak_profile_lower_than_strong(self):
        engine = EligibilityScoringEngine()
        strong = engine.score(_scholarship(), _profile(cgpa=Decimal("3.8"), ielts=Decimal("7.5")))
        weak = engine.score(
            _scholarship(minimum_gpa=Decimal("3.8"), minimum_ielts=Decimal("7.5")),
            _profile(cgpa=Decimal("2.5"), ielts=Decimal("5.5")),
        )
        assert strong.scholarship_score > weak.scholarship_score

    def test_batch_scoring(self):
        engine = EligibilityScoringEngine()
        scholarships = [_scholarship(), _scholarship(title="Other Scholarship", country="Canada")]
        results = engine.score_batch(scholarships, _profile())
        assert len(results) == 2


class TestExplainer:
    def test_generates_explanation(self):
        engine = EligibilityScoringEngine()
        scholarship = _scholarship()
        profile = _profile()
        breakdown = engine.score(scholarship, profile)
        explanation = ScholarshipExplanationEngine().explain(scholarship, profile, breakdown)
        assert "GPA" in explanation or "gpa" in explanation.lower()
        assert "Match" in explanation or "match" in explanation.lower()


class TestScholarshipCache:
    def test_cache_key_prefix(self):
        cache = RecommendationCache(prefix="rec:scholarships:")
        key = cache.build_cache_key({"cgpa": "3.5", "major": "CS"})
        assert key.startswith("rec:scholarships:")
