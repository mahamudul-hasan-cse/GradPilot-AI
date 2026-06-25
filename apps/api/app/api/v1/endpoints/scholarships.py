from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.scholarship import ScholarshipResponse
from app.services.scholarship import ScholarshipService

router = APIRouter(prefix="/scholarships", tags=["Scholarships"])


@router.get("", response_model=PaginatedResponse[ScholarshipResponse])
async def list_scholarships(
    country: str | None = Query(default=None),
    q: str | None = Query(default=None, description="Search by title or provider"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ScholarshipResponse]:
    service = ScholarshipService(db)
    return await service.search_scholarships(
        country=country,
        query=q,
        skip=skip,
        limit=limit,
    )


@router.get("/{scholarship_id}", response_model=ScholarshipResponse)
async def get_scholarship(
    scholarship_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ScholarshipResponse:
    service = ScholarshipService(db)
    return await service.get_scholarship(scholarship_id)
