from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile_analysis import ProfileAnalysis
from app.repositories.base import BaseRepository


class ProfileAnalysisRepository(BaseRepository[ProfileAnalysis]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ProfileAnalysis)

    async def get_analytics(self) -> dict:
        total = await self.db.scalar(select(func.count()).select_from(ProfileAnalysis)) or 0
        avg_admission = await self.db.scalar(select(func.avg(ProfileAnalysis.admission_readiness_score)))
        avg_scholarship = await self.db.scalar(select(func.avg(ProfileAnalysis.scholarship_readiness_score)))
        avg_employability = await self.db.scalar(select(func.avg(ProfileAnalysis.employability_score)))
        cache_hits = await self.db.scalar(
            select(func.count()).select_from(ProfileAnalysis).where(ProfileAnalysis.cache_hit.is_(True))
        ) or 0

        tier_rows = await self.db.execute(
            select(ProfileAnalysis.recommended_university_tier, func.count())
            .where(ProfileAnalysis.recommended_university_tier.isnot(None))
            .group_by(ProfileAnalysis.recommended_university_tier)
        )
        tier_distribution = {row[0]: row[1] for row in tier_rows.all()}

        analyzer_rows = await self.db.execute(
            select(ProfileAnalysis.analyzer_type, func.count()).group_by(ProfileAnalysis.analyzer_type)
        )
        analyzer_distribution = {row[0]: row[1] for row in analyzer_rows.all()}

        return {
            "total_analyses": total,
            "avg_admission_readiness_score": round(float(avg_admission or 0), 2),
            "avg_scholarship_readiness_score": round(float(avg_scholarship or 0), 2),
            "avg_employability_score": round(float(avg_employability or 0), 2),
            "cache_hit_rate": round(cache_hits / max(total, 1) * 100, 2),
            "tier_distribution": tier_distribution,
            "analyzer_distribution": analyzer_distribution,
        }

    async def get_recent(self, *, limit: int = 20) -> list[ProfileAnalysis]:
        result = await self.db.execute(
            select(ProfileAnalysis).order_by(ProfileAnalysis.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
