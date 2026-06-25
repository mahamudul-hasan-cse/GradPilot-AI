from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

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
        return PaginatedResponse(
            items=items,
            total=len(items),
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
