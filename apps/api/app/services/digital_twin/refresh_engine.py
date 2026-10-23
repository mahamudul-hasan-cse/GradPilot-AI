"""Refresh recommendations when profile changes."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.student_profile import StudentProfileRepository
from app.schemas.profile_intelligence import ProfileAnalysisRequest
from app.schemas.recommendation import UniversityRecommendationRequest
from app.schemas.scholarship_recommendation import ScholarshipRecommendationRequest
from app.services.digital_twin.aggregator import TwinAggregator
from app.services.digital_twin.types import TwinEventType
from app.services.profile_intelligence.service import ProfileIntelligenceService
from app.services.recommendation.engine import UniversityRecommendationEngine
from app.services.scholarship_recommendation.service import ScholarshipRecommendationService


class RecommendationRefreshEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = StudentProfileRepository(db)
        self.aggregator = TwinAggregator(db)
        self.profile_intel = ProfileIntelligenceService(db)
        self.uni_engine = UniversityRecommendationEngine(db)
        self.scholarship_svc = ScholarshipRecommendationService(db)

    async def refresh_all(self, user_id: UUID) -> dict:
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return {"refreshed": False, "reason": "no_profile"}

        params = self.aggregator.profile_to_analysis_request(profile)
        budget = Decimal(str(profile.budget_max or 50000))

        analysis = await self.profile_intel.analyze(
            ProfileAnalysisRequest(**params),
            user_id=user_id,
        )
        universities = await self.uni_engine.recommend(
            UniversityRecommendationRequest(
                cgpa=params["cgpa"],
                ielts=params["ielts"],
                budget=budget,
                country_preference=(profile.target_countries or [None])[0],
                major=params["major"],
                work_experience_years=params.get("work_experience_years", 0),
                use_cache=False,
            ),
            user_id=user_id,
        )
        scholarships = await self.scholarship_svc.recommend(
            ScholarshipRecommendationRequest(
                cgpa=params["cgpa"],
                ielts=params["ielts"],
                degree_level=params["degree_level"],
                major=params["major"],
                country_preference=(profile.target_countries or [None])[0],
                nationality=params.get("nationality"),
                work_experience_years=params.get("work_experience_years", 0),
                use_cache=False,
            ),
            user_id=user_id,
        )

        return {
            "refreshed": True,
            "services": {
                "profile_intelligence": {
                    "admission_readiness_score": analysis.admission_readiness_score,
                    "history_id": str(analysis.history_id) if analysis.history_id else None,
                },
                "university_recommendation": {
                    "total_matches": (
                        len(universities.recommendations.safe)
                        + len(universities.recommendations.target)
                        + len(universities.recommendations.ambitious)
                    ),
                    "history_id": str(universities.history_id) if universities.history_id else None,
                },
                "scholarship_matching": {
                    "total_matches": len(scholarships.matches),
                    "history_id": str(scholarships.history_id) if scholarships.history_id else None,
                },
            },
            "events_published": [
                TwinEventType.ANALYSIS_COMPLETED,
                TwinEventType.RECOMMENDATION_GENERATED,
                TwinEventType.SCHOLARSHIP_MATCHED,
            ],
        }
