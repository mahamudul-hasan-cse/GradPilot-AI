from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, String, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.university import University
from app.repositories.university import UniversityRepository
from app.schemas.common import PaginatedResponse
from app.schemas.university import ProgramResponse, UniversityDetailResponse, UniversityResponse


class UniversityService:
    def __init__(self, db: AsyncSession):
        self.university_repo = UniversityRepository(db)

    async def search_universities(
        self,
        *,
        country: str | None = None,
        query: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> PaginatedResponse[UniversityResponse]:
        universities = await self.university_repo.search(
            country=country,
            query=query,
            skip=skip,
            limit=limit,
        )
        items = [UniversityResponse.model_validate(u) for u in universities]

        # Get true total for accurate pagination
        count_stmt = select(func.count()).select_from(University).where(University.is_active.is_(True))
        if country:
            count_stmt = count_stmt.where(University.country.ilike(f"%{country}%"))
        if query:
            pattern = f"%{query}%"
            count_stmt = count_stmt.where(
                or_(
                    University.name.ilike(pattern),
                    University.city.ilike(pattern),
                    University.country.ilike(pattern),
                    University.search_text.ilike(pattern),
                    cast(University.programs, String).ilike(pattern),
                )
            )
        total_result = await self.university_repo.db.execute(count_stmt)
        total = total_result.scalar_one()

        return PaginatedResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_university(self, university_id: UUID) -> UniversityDetailResponse:
        university = await self.university_repo.get_with_programs(university_id)
        if university is None or not university.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="University not found",
            )
        base = UniversityResponse.model_validate(university)
        detailed_programs = [
            ProgramResponse.model_validate(p) for p in university.program_records
        ]
        return UniversityDetailResponse(**base.model_dump(), detailed_programs=detailed_programs)
