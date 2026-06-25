from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.university import University
from app.repositories.base import BaseRepository


@dataclass
class UniversityFilterParams:
    country: str | None = None
    city: str | None = None
    major: str | None = None
    min_ranking: int | None = None
    max_ranking: int | None = None
    max_tuition: Decimal | None = None
    min_tuition: Decimal | None = None
    max_gpa_required: Decimal | None = None
    min_gpa_required: Decimal | None = None
    max_ielts_required: Decimal | None = None
    scholarships_available: bool | None = None
    skip: int = 0
    limit: int = 20


class UniversityRepository(BaseRepository[University]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, University)

    def _active_stmt(self):
        return select(University).where(University.is_active.is_(True))

    def _apply_filters(self, stmt, params: UniversityFilterParams):
        if params.country:
            stmt = stmt.where(University.country.ilike(f"%{params.country}%"))
        if params.city:
            stmt = stmt.where(University.city.ilike(f"%{params.city}%"))
        if params.major:
            major_pattern = f"%{params.major}%"
            stmt = stmt.where(
                or_(
                    University.majors.any(params.major),
                    cast(University.programs, String).ilike(major_pattern),
                    University.search_text.ilike(major_pattern),
                )
            )
        if params.min_ranking is not None:
            stmt = stmt.where(University.ranking >= params.min_ranking)
        if params.max_ranking is not None:
            stmt = stmt.where(University.ranking <= params.max_ranking)
        if params.max_tuition is not None:
            stmt = stmt.where(
                or_(University.tuition_fee.is_(None), University.tuition_fee <= params.max_tuition)
            )
        if params.min_tuition is not None:
            stmt = stmt.where(University.tuition_fee >= params.min_tuition)
        if params.max_gpa_required is not None:
            stmt = stmt.where(
                or_(University.minimum_gpa.is_(None), University.minimum_gpa <= params.max_gpa_required)
            )
        if params.min_gpa_required is not None:
            stmt = stmt.where(University.minimum_gpa >= params.min_gpa_required)
        if params.max_ielts_required is not None:
            stmt = stmt.where(
                or_(
                    University.minimum_ielts.is_(None),
                    University.minimum_ielts <= params.max_ielts_required,
                )
            )
        if params.scholarships_available is not None:
            stmt = stmt.where(University.scholarships_available.is_(params.scholarships_available))
        return stmt

    async def filter_universities(self, params: UniversityFilterParams) -> tuple[list[University], int]:
        base = self._apply_filters(self._active_stmt(), params)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            base.order_by(University.ranking.asc().nullslast(), University.name.asc())
            .offset(params.skip)
            .limit(params.limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def search(
        self,
        *,
        country: str | None = None,
        query: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[University]:
        params = UniversityFilterParams(country=country, skip=skip, limit=limit)
        stmt = self._apply_filters(self._active_stmt(), params)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    University.name.ilike(pattern),
                    University.city.ilike(pattern),
                    University.country.ilike(pattern),
                    University.search_text.ilike(pattern),
                    cast(University.programs, String).ilike(pattern),
                )
            )
        stmt = stmt.order_by(University.ranking.asc().nullslast()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_text_query(
        self,
        query: str,
        *,
        country: str | None = None,
        major: str | None = None,
        limit: int = 20,
    ) -> list[University]:
        params = UniversityFilterParams(country=country, major=major, limit=limit)
        stmt = self._apply_filters(self._active_stmt(), params)
        pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                University.name.ilike(pattern),
                University.city.ilike(pattern),
                University.description.ilike(pattern),
                University.search_text.ilike(pattern),
                cast(University.programs, String).ilike(pattern),
            )
        )
        stmt = stmt.order_by(University.ranking.asc().nullslast()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_candidates_for_recommendation(
        self,
        *,
        country: str | None = None,
        major: str | None = None,
        max_budget: Decimal | None = None,
        limit: int = 100,
    ) -> list[University]:
        params = UniversityFilterParams(
            country=country,
            major=major,
            max_tuition=max_budget,
            limit=limit,
        )
        stmt = self._apply_filters(self._active_stmt(), params)
        stmt = stmt.order_by(University.ranking.asc().nullslast()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ids(self, university_ids: Sequence[UUID]) -> list[University]:
        if not university_ids:
            return []
        stmt = select(University).where(University.id.in_(university_ids), University.is_active.is_(True))
        result = await self.db.execute(stmt)
        universities = list(result.scalars().all())
        order = {uid: idx for idx, uid in enumerate(university_ids)}
        universities.sort(key=lambda u: order.get(u.id, 999))
        return universities

    async def get_with_programs(self, university_id) -> University | None:
        result = await self.db.execute(
            select(University)
            .options(selectinload(University.program_records))
            .where(University.id == university_id)
        )
        return result.scalar_one_or_none()

    async def get_all_active(self) -> list[University]:
        result = await self.db.execute(
            self._active_stmt().order_by(University.ranking.asc().nullslast())
        )
        return list(result.scalars().all())
