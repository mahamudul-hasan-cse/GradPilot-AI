"""Student Profile Intelligence Engine."""

from app.services.profile_intelligence.analyzer import RuleBasedProfileAnalyzer
from app.services.profile_intelligence.base import ProfileAnalyzer, ProfileAnalysisResult, StudentAnalysisProfile
from app.services.profile_intelligence.recommendations import RecommendationGenerator
from app.services.profile_intelligence.service import ProfileIntelligenceService

__all__ = [
    "ProfileAnalyzer",
    "ProfileAnalysisResult",
    "ProfileIntelligenceService",
    "RecommendationGenerator",
    "RuleBasedProfileAnalyzer",
    "StudentAnalysisProfile",
]
