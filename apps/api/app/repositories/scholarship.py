from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scholarship import Scholarship
from app.repositories.base import BaseRepository


class ScholarshipRepository(BaseRepository[Scholarship]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Scholarship)

    async def search(
        self,
        *,
        country: str | None = None,
        query: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Scholarship]:
        stmt = select(Scholarship).where(Scholarship.is_active.is_(True))

        if country:
            stmt = stmt.where(Scholarship.country.ilike(f"%{country}%"))
        if query:
            stmt = stmt.where(
                or_(
                    Scholarship.title.ilike(f"%{query}%"),
                    Scholarship.provider.ilike(f"%{query}%"),
                )
            )

        stmt = stmt.order_by(Scholarship.deadline.asc().nullslast()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_candidates_for_matching(
        self,
        *,
        country: str | None = None,
        degree_level: str | None = None,
        limit: int = 5000,
    ) -> list[Scholarship]:
        """Fetch active scholarships with indexed pre-filters for efficient batch scoring."""
        stmt = select(Scholarship).where(Scholarship.is_active.is_(True))

        if country:
            stmt = stmt.where(
                or_(
                    Scholarship.country.ilike(f"%{country}%"),
                    Scholarship.country.is_(None),
                )
            )
        if degree_level:
            stmt = stmt.where(
                or_(
                    Scholarship.degree_level.ilike(f"%{degree_level}%"),
                    Scholarship.degree_level.is_(None),
                )
            )

        stmt = stmt.order_by(Scholarship.deadline.asc().nullslast()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_active(self) -> int:
        result = await self.db.scalar(
            select(func.count()).select_from(Scholarship).where(Scholarship.is_active.is_(True))
        )
        return result or 0
