"""Scholarship Recommendation Service — match, rank, cache, and persist."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scholarship_recommendation import ScholarshipRecommendationHistory
from app.repositories.scholarship import ScholarshipRepository
from app.repositories.scholarship_recommendation import ScholarshipRecommendationHistoryRepository
from app.schemas.scholarship import ScholarshipResponse
from app.schemas.scholarship_recommendation import (
    MatchedScholarship,
    ScholarshipMatchGroups,
    ScholarshipRecommendationAnalytics,
    ScholarshipRecommendationRequest,
    ScholarshipRecommendationResponse,
    ScholarshipScoreDetail,
)
from app.services.recommendation.cache import RecommendationCache
from app.services.scholarship_recommendation.explainer import ScholarshipExplanationEngine
from app.services.scholarship_recommendation.scoring import (
    WEIGHTS,
    EligibilityScoringEngine,
    ScholarshipStudentProfile,
)


class ScholarshipRecommendationService:
    CACHE_PREFIX = "rec:scholarships:"

    def __init__(self, db: AsyncSession, cache: RecommendationCache | None = None):
        self.db = db
        self.scholarship_repo = ScholarshipRepository(db)
        self.history_repo = ScholarshipRecommendationHistoryRepository(db)
        self.scoring_engine = EligibilityScoringEngine()
        self.explainer = ScholarshipExplanationEngine()
        self.cache = cache or RecommendationCache(prefix=self.CACHE_PREFIX)

    def _to_profile(self, request: ScholarshipRecommendationRequest) -> ScholarshipStudentProfile:
        return ScholarshipStudentProfile(
            cgpa=request.cgpa,
            ielts=request.ielts,
            degree_level=request.degree_level,
            major=request.major,
            country_preference=request.country_preference,
            has_research_experience=request.has_research_experience,
            work_experience_years=request.work_experience_years,
            nationality=request.nationality,
        )

    async def recommend(
        self,
        request: ScholarshipRecommendationRequest,
        *,
        user_id: UUID | None = None,
    ) -> ScholarshipRecommendationResponse:
        cache_key = self.cache.build_cache_key(request.model_dump(mode="json"))

        if request.use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                response = ScholarshipRecommendationResponse.model_validate(cached)
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

        profile = self._to_profile(request)
        candidates = await self.scholarship_repo.get_candidates_for_matching(
            country=request.country_preference,
            degree_level=request.degree_level,
            limit=5000,
        )

        scored_batch = self.scoring_engine.score_batch(candidates, profile)
        matches: list[MatchedScholarship] = []

        for scholarship, breakdown in scored_batch:
            if breakdown.scholarship_score < request.min_score:
                continue
            explanation = self.explainer.explain(scholarship, profile, breakdown)
            matches.append(
                MatchedScholarship(
                    scholarship=ScholarshipResponse.model_validate(scholarship),
                    score=ScholarshipScoreDetail(
                        academic_match=breakdown.academic_match,
                        language_match=breakdown.language_match,
                        degree_match=breakdown.degree_match,
                        country_match=breakdown.country_match,
                        research_match=breakdown.research_match,
                        work_experience_match=breakdown.work_experience_match,
                        scholarship_score=breakdown.scholarship_score,
                        eligibility_probability=breakdown.eligibility_probability,
                        match_category=breakdown.match_category,
                    ),
                    explanation=explanation,
                )
            )

        matches.sort(key=lambda m: m.score.scholarship_score, reverse=True)
        matches = matches[: request.limit]

        grouped = self._group_matches(matches)
        response = ScholarshipRecommendationResponse(
            request=request,
            matches=matches,
            grouped=grouped,
            total_candidates_evaluated=len(candidates),
            cache_hit=False,
            scoring_weights={
                "academic_match": WEIGHTS["academic"],
                "language_match": WEIGHTS["language"],
                "degree_match": WEIGHTS["degree"],
                "country_match": WEIGHTS["country"],
                "research_match": WEIGHTS["research"],
                "work_experience_match": WEIGHTS["work_experience"],
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

    def _group_matches(self, matches: list[MatchedScholarship]) -> ScholarshipMatchGroups:
        groups = ScholarshipMatchGroups()
        for match in matches:
            cat = match.score.match_category
            if cat == "excellent":
                groups.excellent.append(match)
            elif cat == "strong":
                groups.strong.append(match)
            elif cat == "possible":
                groups.possible.append(match)
            else:
                groups.low.append(match)
        return groups

    async def _save_history(
        self,
        *,
        user_id: UUID | None,
        request: ScholarshipRecommendationRequest,
        response: ScholarshipRecommendationResponse,
        cache_key: str,
        cache_hit: bool,
    ) -> ScholarshipRecommendationHistory:
        counts = {"excellent": 0, "strong": 0, "possible": 0, "low": 0}
        for m in response.matches:
            counts[m.score.match_category] = counts.get(m.score.match_category, 0) + 1

        avg_score = (
            sum(m.score.scholarship_score for m in response.matches) / len(response.matches)
            if response.matches
            else None
        )
        avg_prob = (
            sum(m.score.eligibility_probability for m in response.matches) / len(response.matches)
            if response.matches
            else None
        )

        history = ScholarshipRecommendationHistory(
            user_id=user_id,
            cache_key=cache_key,
            request_payload=request.model_dump(mode="json"),
            response_summary={
                "total_candidates_evaluated": response.total_candidates_evaluated,
                "matches_returned": len(response.matches),
                "cache_hit": cache_hit,
                "match_distribution": counts,
            },
            avg_scholarship_score=avg_score,
            avg_eligibility_probability=avg_prob,
            excellent_count=counts["excellent"],
            strong_count=counts["strong"],
            possible_count=counts["possible"],
            low_count=counts["low"],
            candidates_evaluated=response.total_candidates_evaluated,
            cache_hit=cache_hit,
        )
        return await self.history_repo.create(history)

    async def get_analytics(self) -> ScholarshipRecommendationAnalytics:
        analytics = await self.history_repo.get_analytics()
        total_scholarships = await self.scholarship_repo.count_active()
        recent = await self.history_repo.get_recent(limit=10)
        return ScholarshipRecommendationAnalytics(
            total_recommendations=analytics["total_recommendations"],
            avg_scholarship_score=analytics["avg_scholarship_score"],
            avg_eligibility_probability=analytics["avg_eligibility_probability"],
            cache_hit_rate=analytics["cache_hit_rate"],
            match_distribution=analytics["match_distribution"],
            total_active_scholarships=total_scholarships,
            recent_requests=[
                {
                    "id": str(r.id),
                    "avg_score": float(r.avg_scholarship_score or 0),
                    "matches_returned": r.excellent_count + r.strong_count + r.possible_count + r.low_count,
                    "cache_hit": r.cache_hit,
                    "created_at": r.created_at.isoformat(),
                }
                for r in recent
            ],
        )
