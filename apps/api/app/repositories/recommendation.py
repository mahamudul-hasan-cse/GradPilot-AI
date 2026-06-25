from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import RecommendationHistory
from app.repositories.base import BaseRepository


class RecommendationHistoryRepository(BaseRepository[RecommendationHistory]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, RecommendationHistory)

    async def get_by_user(self, user_id: UUID, *, limit: int = 20) -> list[RecommendationHistory]:
        result = await self.db.execute(
            select(RecommendationHistory)
            .where(RecommendationHistory.user_id == user_id)
            .order_by(RecommendationHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
