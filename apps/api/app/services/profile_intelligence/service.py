"""Profile Intelligence Service — orchestrates analysis, cache, and history."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile_analysis import ProfileAnalysis
from app.repositories.profile_analysis import ProfileAnalysisRepository
from app.schemas.profile_intelligence import (
    ProfileAnalysisAnalytics,
    ProfileAnalysisRequest,
    ProfileAnalysisResponse,
    ScoreExplanation,
)
from app.services.profile_intelligence.analyzer import RuleBasedProfileAnalyzer
from app.services.profile_intelligence.base import ProfileAnalyzer, StudentAnalysisProfile
from app.services.recommendation.cache import RecommendationCache

ANALYZER_REGISTRY: dict[str, type[ProfileAnalyzer]] = {
    "rule_based": RuleBasedProfileAnalyzer,
}


class ProfileIntelligenceService:
    CACHE_PREFIX = "profile:analysis:"

    def __init__(self, db: AsyncSession, cache: RecommendationCache | None = None):
        self.db = db
        self.history_repo = ProfileAnalysisRepository(db)
        self.cache = cache or RecommendationCache(prefix=self.CACHE_PREFIX)

    def _get_analyzer(self, analyzer_type: str) -> ProfileAnalyzer:
        if analyzer_type not in ANALYZER_REGISTRY:
            raise ValueError(f"Unsupported analyzer type: {analyzer_type}")
        return ANALYZER_REGISTRY[analyzer_type]()

    def _to_profile(self, request: ProfileAnalysisRequest) -> StudentAnalysisProfile:
        return StudentAnalysisProfile(
            cgpa=request.cgpa,
            ielts=request.ielts,
            degree_level=request.degree_level,
            major=request.major,
            country_preferences=request.country_preferences,
            work_experience_years=request.work_experience_years,
            has_research_experience=request.has_research_experience,
            publications_count=request.publications_count,
            certifications=request.certifications,
            target_intake=request.target_intake,
        )

    def _to_response(self, result, *, cache_hit: bool = False, history_id: UUID | None = None) -> ProfileAnalysisResponse:
        explanations = {
            key: ScoreExplanation(**value) for key, value in result.score_explanations.items()
        }
        return ProfileAnalysisResponse(
            admission_readiness_score=result.admission_readiness_score,
            scholarship_readiness_score=result.scholarship_readiness_score,
            employability_score=result.employability_score,
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            missing_requirements=result.missing_requirements,
            recommended_actions=result.recommended_actions,
            recommended_countries=result.recommended_countries,
            recommended_university_tier=result.recommended_university_tier,
            profile_summary=result.profile_summary,
            score_explanations=explanations,
            analyzer_type=result.analyzer_type,
            cache_hit=cache_hit,
            history_id=history_id,
        )

    async def analyze(
        self,
        request: ProfileAnalysisRequest,
        *,
        user_id: UUID | None = None,
    ) -> ProfileAnalysisResponse:
        cache_key = self.cache.build_cache_key(request.model_dump(mode="json"))

        if request.use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                response = ProfileAnalysisResponse.model_validate(cached)
                response.cache_hit = True
                history = await self._save_history(
                    user_id=user_id,
                    request=request,
                    response=response,
                    cache_key=cache_key,
                    cache_hit=True,
                )
                response.history_id = history.id
                return response

        analyzer = self._get_analyzer(request.analyzer_type)
        profile = self._to_profile(request)
        result = analyzer.analyze(profile)
        response = self._to_response(result, cache_hit=False)

        if request.use_cache:
            await self.cache.set(cache_key, response.model_dump(mode="json"))

        history = await self._save_history(
            user_id=user_id,
            request=request,
            response=response,
            cache_key=cache_key,
            cache_hit=False,
        )
        response.history_id = history.id
        return response

    async def _save_history(
        self,
        *,
        user_id: UUID | None,
        request: ProfileAnalysisRequest,
        response: ProfileAnalysisResponse,
        cache_key: str,
        cache_hit: bool,
    ) -> ProfileAnalysis:
        record = ProfileAnalysis(
            user_id=user_id,
            cache_key=cache_key,
            analyzer_type=response.analyzer_type,
            request_payload=request.model_dump(mode="json"),
            response_summary={
                "admission_readiness_score": response.admission_readiness_score,
                "scholarship_readiness_score": response.scholarship_readiness_score,
                "employability_score": response.employability_score,
                "recommended_university_tier": response.recommended_university_tier,
                "strengths_count": len(response.strengths),
                "weaknesses_count": len(response.weaknesses),
                "actions_count": len(response.recommended_actions),
                "cache_hit": cache_hit,
            },
            admission_readiness_score=response.admission_readiness_score,
            scholarship_readiness_score=response.scholarship_readiness_score,
            employability_score=response.employability_score,
            recommended_university_tier=response.recommended_university_tier,
            cache_hit=cache_hit,
        )
        return await self.history_repo.create(record)

    async def get_analytics(self) -> ProfileAnalysisAnalytics:
        analytics = await self.history_repo.get_analytics()
        recent = await self.history_repo.get_recent(limit=10)
        return ProfileAnalysisAnalytics(
            total_analyses=analytics["total_analyses"],
            avg_admission_readiness_score=analytics["avg_admission_readiness_score"],
            avg_scholarship_readiness_score=analytics["avg_scholarship_readiness_score"],
            avg_employability_score=analytics["avg_employability_score"],
            cache_hit_rate=analytics["cache_hit_rate"],
            tier_distribution=analytics["tier_distribution"],
            analyzer_distribution=analytics["analyzer_distribution"],
            recent_analyses=[
                {
                    "id": str(r.id),
                    "admission_score": float(r.admission_readiness_score or 0),
                    "scholarship_score": float(r.scholarship_readiness_score or 0),
                    "employability_score": float(r.employability_score or 0),
                    "tier": r.recommended_university_tier,
                    "analyzer_type": r.analyzer_type,
                    "cache_hit": r.cache_hit,
                    "created_at": r.created_at.isoformat(),
                }
                for r in recent
            ],
        )
