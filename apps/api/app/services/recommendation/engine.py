"""University Recommendation Engine — orchestrates scoring, explanation, cache, and history."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import RecommendationHistory
from app.repositories.recommendation import RecommendationHistoryRepository
from app.repositories.university import UniversityRepository
from app.schemas.recommendation import (
    RecommendationScoreBreakdown,
    RecommendationTierGroup,
    RecommendedUniversity,
    UniversityRecommendationRequest,
    UniversityRecommendationResponse,
)
from app.schemas.university import UniversityResponse
from app.services.recommendation.cache import RecommendationCache
from app.services.recommendation.explainer import RecommendationExplainer
from app.services.recommendation.scoring import (
    WEIGHTS,
    StudentRecommendationProfile,
    score_university,
)


class UniversityRecommendationEngine:
    def __init__(
        self,
        db: AsyncSession,
        cache: RecommendationCache | None = None,
    ):
        self.db = db
        self.university_repo = UniversityRepository(db)
        self.history_repo = RecommendationHistoryRepository(db)
        self.cache = cache or RecommendationCache()
        self.explainer = RecommendationExplainer()

    def _to_student_profile(self, request: UniversityRecommendationRequest) -> StudentRecommendationProfile:
        return StudentRecommendationProfile(
            cgpa=request.cgpa,
            ielts=request.ielts,
            budget=request.budget,
            major=request.major,
            country_preference=request.country_preference,
            work_experience_years=request.work_experience_years,
            has_research_experience=request.has_research_experience,
        )

    def _cache_payload(self, request: UniversityRecommendationRequest) -> dict:
        return request.model_dump(mode="json")

    async def recommend(
        self,
        request: UniversityRecommendationRequest,
        *,
        user_id: UUID | None = None,
    ) -> UniversityRecommendationResponse:
        cache_key = self.cache.build_cache_key(self._cache_payload(request))

        if request.use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                response = UniversityRecommendationResponse.model_validate(cached)
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

        profile = self._to_student_profile(request)
        candidates = await self.university_repo.get_candidates_for_recommendation(
            country=request.country_preference,
            major=request.major,
            max_budget=request.budget * Decimal("1.5"),
            limit=200,
        )

        scored: list[RecommendedUniversity] = []
        for university in candidates:
            breakdown = score_university(university, profile)
            explanation = self.explainer.explain(university, profile, breakdown)
            scored.append(
                RecommendedUniversity(
                    university=UniversityResponse.model_validate(university),
                    score_breakdown=RecommendationScoreBreakdown(
                        academic_match=breakdown.academic_match,
                        language_match=breakdown.language_match,
                        budget_match=breakdown.budget_match,
                        program_match=breakdown.program_match,
                        scholarship_match=breakdown.scholarship_match,
                        recommendation_score=breakdown.recommendation_score,
                        tier=breakdown.tier,
                    ),
                    explanation=explanation,
                )
            )

        scored.sort(key=lambda r: r.score_breakdown.recommendation_score, reverse=True)

        tiers: dict[str, list[RecommendedUniversity]] = {
            "safe": [],
            "target": [],
            "ambitious": [],
        }
        for item in scored:
            tier = item.score_breakdown.tier
            if len(tiers[tier]) < request.limit_per_tier:
                tiers[tier].append(item)

        response = UniversityRecommendationResponse(
            request=request,
            recommendations=RecommendationTierGroup(
                safe=tiers["safe"],
                target=tiers["target"],
                ambitious=tiers["ambitious"],
            ),
            total_candidates_evaluated=len(scored),
            cache_hit=False,
            scoring_weights={
                "academic_match": WEIGHTS["academic"],
                "language_match": WEIGHTS["language"],
                "budget_match": WEIGHTS["budget"],
                "program_match": WEIGHTS["program"],
                "scholarship_match": WEIGHTS["scholarship"],
            },
        )

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
        request: UniversityRecommendationRequest,
        response: UniversityRecommendationResponse,
        cache_key: str,
        cache_hit: bool,
    ) -> RecommendationHistory:
        all_items = (
            response.recommendations.safe
            + response.recommendations.target
            + response.recommendations.ambitious
        )
        avg_score = (
            sum(i.score_breakdown.recommendation_score for i in all_items) / len(all_items)
            if all_items
            else None
        )

        history = RecommendationHistory(
            user_id=user_id,
            cache_key=cache_key,
            request_payload=request.model_dump(mode="json"),
            response_summary={
                "total_candidates_evaluated": response.total_candidates_evaluated,
                "safe_count": len(response.recommendations.safe),
                "target_count": len(response.recommendations.target),
                "ambitious_count": len(response.recommendations.ambitious),
                "cache_hit": cache_hit,
            },
            total_score_avg=avg_score,
            safe_count=len(response.recommendations.safe),
            target_count=len(response.recommendations.target),
            ambitious_count=len(response.recommendations.ambitious),
            candidates_evaluated=response.total_candidates_evaluated,
            cache_hit=cache_hit,
        )
        return await self.history_repo.create(history)
