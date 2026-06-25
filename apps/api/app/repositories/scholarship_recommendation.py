from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scholarship_recommendation import ScholarshipRecommendationHistory
from app.repositories.base import BaseRepository


class ScholarshipRecommendationHistoryRepository(BaseRepository[ScholarshipRecommendationHistory]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ScholarshipRecommendationHistory)

    async def get_analytics(self) -> dict:
        total = await self.db.scalar(select(func.count()).select_from(ScholarshipRecommendationHistory)) or 0
        avg_score = await self.db.scalar(
            select(func.avg(ScholarshipRecommendationHistory.avg_scholarship_score))
        )
        avg_prob = await self.db.scalar(
            select(func.avg(ScholarshipRecommendationHistory.avg_eligibility_probability))
        )
        cache_hits = await self.db.scalar(
            select(func.count())
            .select_from(ScholarshipRecommendationHistory)
            .where(ScholarshipRecommendationHistory.cache_hit.is_(True))
        ) or 0
        sum_excellent = await self.db.scalar(
            select(func.sum(ScholarshipRecommendationHistory.excellent_count))
        ) or 0
        sum_strong = await self.db.scalar(
            select(func.sum(ScholarshipRecommendationHistory.strong_count))
        ) or 0
        sum_possible = await self.db.scalar(
            select(func.sum(ScholarshipRecommendationHistory.possible_count))
        ) or 0
        sum_low = await self.db.scalar(
            select(func.sum(ScholarshipRecommendationHistory.low_count))
        ) or 0

        return {
            "total_recommendations": total,
            "avg_scholarship_score": round(float(avg_score or 0), 2),
            "avg_eligibility_probability": round(float(avg_prob or 0), 4),
            "cache_hit_rate": round(cache_hits / max(total, 1) * 100, 2),
            "match_distribution": {
                "excellent": int(sum_excellent),
                "strong": int(sum_strong),
                "possible": int(sum_possible),
                "low": int(sum_low),
            },
        }

    async def get_recent(self, *, limit: int = 20) -> list[ScholarshipRecommendationHistory]:
        result = await self.db.execute(
            select(ScholarshipRecommendationHistory)
            .order_by(ScholarshipRecommendationHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
