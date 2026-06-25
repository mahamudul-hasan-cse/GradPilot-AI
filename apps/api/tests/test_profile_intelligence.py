"""Tests for the Student Profile Intelligence Engine."""

from decimal import Decimal

import pytest

from app.services.profile_intelligence.analyzer import (
    ADMISSION_WEIGHTS,
    EMPLOYABILITY_WEIGHTS,
    SCHOLARSHIP_WEIGHTS,
    RuleBasedProfileAnalyzer,
    classify_university_tier,
    score_academic,
    score_language,
    score_research,
    weighted_score,
)
from app.services.profile_intelligence.base import StudentAnalysisProfile
from app.services.profile_intelligence.recommendations import RecommendationGenerator
from app.services.recommendation.cache import RecommendationCache


def _profile(**kwargs) -> StudentAnalysisProfile:
    defaults = {
        "cgpa": Decimal("3.5"),
        "ielts": Decimal("7.0"),
        "degree_level": "masters",
        "major": "Computer Science",
        "country_preferences": ["United States", "Canada"],
        "work_experience_years": 2,
        "has_research_experience": True,
        "publications_count": 1,
        "certifications": ["AWS Certified"],
        "target_intake": "Fall 2026",
    }
    defaults.update(kwargs)
    return StudentAnalysisProfile(**defaults)


class TestWeights:
    def test_admission_weights_sum_to_one(self):
        assert sum(ADMISSION_WEIGHTS.values()) == pytest.approx(1.0)

    def test_scholarship_weights_sum_to_one(self):
        assert sum(SCHOLARSHIP_WEIGHTS.values()) == pytest.approx(1.0)

    def test_employability_weights_sum_to_one(self):
        assert sum(EMPLOYABILITY_WEIGHTS.values()) == pytest.approx(1.0)


class TestScoringFunctions:
    def test_strong_academic_score(self):
        assert score_academic(Decimal("3.8"), "masters") >= 0.85

    def test_weak_academic_score(self):
        assert score_academic(Decimal("2.5"), "masters") < 0.65

    def test_ielts_meets_masters_benchmark(self):
        assert score_language(Decimal("7.0"), "masters") >= 0.80

    def test_research_with_publications(self):
        profile = _profile(has_research_experience=True, publications_count=2)
        assert score_research(profile) >= 0.70


class TestUniversityTier:
    def test_top_tier(self):
        assert "Top Tier" in classify_university_tier(90)

    def test_safety_tier(self):
        assert "Foundation" in classify_university_tier(40)


class TestRuleBasedProfileAnalyzer:
    def test_strong_profile_high_scores(self):
        analyzer = RuleBasedProfileAnalyzer()
        result = analyzer.analyze(_profile())
        assert result.admission_readiness_score >= 60
        assert result.scholarship_readiness_score >= 60
        assert result.employability_score >= 60
        assert len(result.strengths) > 0
        assert result.recommended_university_tier
        assert result.profile_summary

    def test_weak_profile_lower_scores(self):
        analyzer = RuleBasedProfileAnalyzer()
        strong = analyzer.analyze(_profile())
        weak = analyzer.analyze(
            _profile(
                cgpa=Decimal("2.4"),
                ielts=Decimal("5.5"),
                has_research_experience=False,
                publications_count=0,
                work_experience_years=0,
                certifications=[],
                country_preferences=[],
                target_intake=None,
            )
        )
        assert strong.admission_readiness_score > weak.admission_readiness_score
        assert len(weak.weaknesses) > 0
        assert len(weak.missing_requirements) > 0

    def test_score_explanations_present(self):
        analyzer = RuleBasedProfileAnalyzer()
        result = analyzer.analyze(_profile())
        assert "admission_readiness" in result.score_explanations
        assert "scholarship_readiness" in result.score_explanations
        assert "employability" in result.score_explanations
        for key in result.score_explanations:
            assert result.score_explanations[key]["explanation"]

    def test_analyzer_type(self):
        analyzer = RuleBasedProfileAnalyzer()
        result = analyzer.analyze(_profile())
        assert result.analyzer_type == "rule_based"


class TestRecommendationGenerator:
    def test_generates_actions_for_weak_profile(self):
        profile = _profile(cgpa=Decimal("2.5"), ielts=Decimal("5.5"), target_intake=None)
        gen = RecommendationGenerator()
        result = gen.generate(
            profile=profile,
            admission_score=45,
            scholarship_score=40,
            weaknesses=["Low GPA"],
            missing=["IELTS 6.5+"],
            components={"academic": 0.4, "language": 0.4, "research": 0.3, "work": 0.3, "completeness": 0.5},
        )
        assert len(result["actions"]) > 0
        assert len(result["countries"]) > 0

    def test_respects_country_preferences(self):
        profile = _profile(country_preferences=["Germany"])
        gen = RecommendationGenerator()
        result = gen.generate(
            profile=profile,
            admission_score=75,
            scholarship_score=70,
            weaknesses=[],
            missing=[],
            components={"academic": 0.8, "language": 0.8, "research": 0.7, "work": 0.7, "completeness": 0.9},
        )
        assert "Germany" in result["countries"]


class TestWeightedScore:
    def test_perfect_components_score_100(self):
        components = {k: 1.0 for k in ADMISSION_WEIGHTS}
        assert weighted_score(components, ADMISSION_WEIGHTS) == 100.0


class TestProfileAnalysisCache:
    def test_cache_key_prefix(self):
        cache = RecommendationCache(prefix="profile:analysis:")
        key = cache.build_cache_key({"cgpa": "3.5", "major": "CS"})
        assert key.startswith("profile:analysis:")
