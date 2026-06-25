from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.university_ranking import (
    StudentProfile,
    classify_tier,
    compute_composite_score,
    rank_university,
    score_budget_match,
    score_gpa_match,
    score_ielts_match,
    score_ranking_preference,
    score_scholarship_availability,
)


class TestScoringFunctions:
    def test_gpa_match_exceeds_minimum(self):
        assert score_gpa_match(Decimal("3.8"), Decimal("3.0")) > 0.8

    def test_gpa_match_below_minimum(self):
        assert score_gpa_match(Decimal("2.5"), Decimal("3.5")) < 0.5

    def test_gpa_match_no_minimum(self):
        assert score_gpa_match(Decimal("3.0"), None) == 0.75

    def test_ielts_match_exceeds_minimum(self):
        assert score_ielts_match(Decimal("7.5"), Decimal("6.5")) > 0.8

    def test_budget_within_budget(self):
        assert score_budget_match(Decimal("50000"), Decimal("40000")) >= 0.85

    def test_budget_over_budget(self):
        assert score_budget_match(Decimal("30000"), Decimal("50000")) == pytest.approx(0.6)

    def test_ranking_top_tier(self):
        assert score_ranking_preference(1) == 1.0
        assert score_ranking_preference(100) == 0.7

    def test_scholarship_bonus(self):
        assert score_scholarship_availability(True) > score_scholarship_availability(False)


class TestCompositeScore:
    def test_weights_sum_to_one(self):
        score = compute_composite_score(
            gpa_match=1.0,
            ielts_match=1.0,
            budget_match=1.0,
            ranking_preference=1.0,
            scholarship_availability=1.0,
        )
        assert score == pytest.approx(1.0)

    def test_partial_scores(self):
        score = compute_composite_score(
            gpa_match=0.5,
            ielts_match=0.5,
            budget_match=0.5,
            ranking_preference=0.5,
            scholarship_availability=0.5,
        )
        assert score == pytest.approx(0.5)


class TestTierClassification:
    def test_safe_tier(self):
        tier = classify_tier(
            composite_score=0.75,
            gpa_match=0.9,
            ielts_match=0.85,
            budget_match=0.88,
            ranking=80,
        )
        assert tier == "safe"

    def test_ambitious_prestigious(self):
        tier = classify_tier(
            composite_score=0.5,
            gpa_match=0.55,
            ielts_match=0.5,
            budget_match=0.45,
            ranking=5,
        )
        assert tier == "ambitious"

    def test_target_tier(self):
        tier = classify_tier(
            composite_score=0.6,
            gpa_match=0.7,
            ielts_match=0.65,
            budget_match=0.6,
            ranking=80,
        )
        assert tier == "target"


class TestRankUniversity:
    def _university(self, **kwargs):
        defaults = {
            "minimum_gpa": Decimal("3.0"),
            "minimum_ielts": Decimal("6.5"),
            "tuition_fee": Decimal("40000"),
            "ranking": 50,
            "scholarships_available": True,
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_rank_returns_all_factors(self):
        profile = StudentProfile(cgpa=Decimal("3.5"), ielts=Decimal("7.0"), budget=Decimal("50000"))
        result = rank_university(self._university(), profile)
        assert 0 <= result.composite_score <= 1
        assert result.tier in {"safe", "target", "ambitious"}
        assert result.gpa_match > 0
        assert result.ielts_match > 0

    def test_affordable_university_scores_higher_budget(self):
        profile = StudentProfile(cgpa=Decimal("3.2"), ielts=Decimal("6.5"), budget=Decimal("25000"))
        affordable = rank_university(
            self._university(tuition_fee=Decimal("20000"), ranking=200),
            profile,
        )
        expensive = rank_university(
            self._university(tuition_fee=Decimal("55000"), ranking=200),
            profile,
        )
        assert affordable.budget_match > expensive.budget_match
