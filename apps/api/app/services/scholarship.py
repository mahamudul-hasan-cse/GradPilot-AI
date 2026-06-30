from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scholarship import Scholarship
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

        # Get true total for accurate pagination
        count_stmt = select(func.count()).select_from(Scholarship).where(Scholarship.is_active.is_(True))
        if country:
            count_stmt = count_stmt.where(Scholarship.country.ilike(f"%{country}%"))
        if query:
            count_stmt = count_stmt.where(
                or_(
                    Scholarship.title.ilike(f"%{query}%"),
                    Scholarship.provider.ilike(f"%{query}%"),
                )
            )
        total_result = await self.scholarship_repo.db.execute(count_stmt)
        total = total_result.scalar_one()

        return PaginatedResponse(
            items=items,
            total=total,
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
