from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.scholarship import ScholarshipRepository
from app.schemas.common import PaginatedResponse
from app.schemas.scholarship import ScholarshipResponse


class ScholarshipService:
    def __init__(self, db: AsyncSession):
        self.scholarship_repo = ScholarshipRepository(db)

    async def search_scholarships(
        self,
        *,
        country: str | None = None,
        query: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> PaginatedResponse[ScholarshipResponse]:
        scholarships = await self.scholarship_repo.search(
            country=country,
            query=query,
            skip=skip,
            limit=limit,
        )
        items = [ScholarshipResponse.model_validate(s) for s in scholarships]
        return PaginatedResponse(
            items=items,
            total=len(items),
            skip=skip,
            limit=limit,
        )

    async def get_scholarship(self, scholarship_id: UUID) -> ScholarshipResponse:
        scholarship = await self.scholarship_repo.get_by_id(scholarship_id)
        if scholarship is None or not scholarship.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scholarship not found",
            )
        return ScholarshipResponse.model_validate(scholarship)
