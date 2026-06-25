from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.discovery import (
    RecommendUniversitiesRequest,
    RecommendUniversitiesResponse,
    SemanticSearchRequest,
    UniversityFilterRequest,
    UniversitySearchRequest,
    UniversitySearchResult,
)
from app.schemas.university import UniversityDetailResponse, UniversityResponse
from app.services.university import UniversityService
from app.services.university_discovery import UniversityDiscoveryService

router = APIRouter(prefix="/universities", tags=["University Discovery"])


@router.get("/filter", response_model=UniversitySearchResult)
async def filter_universities(
    country: str | None = Query(default=None),
    city: str | None = Query(default=None),
    major: str | None = Query(default=None),
    min_ranking: int | None = Query(default=None, ge=1),
    max_ranking: int | None = Query(default=None, ge=1),
    max_tuition: float | None = Query(default=None, ge=0),
    min_tuition: float | None = Query(default=None, ge=0),
    max_gpa_required: float | None = Query(default=None, ge=0, le=4),
    min_gpa_required: float | None = Query(default=None, ge=0, le=4),
    max_ielts_required: float | None = Query(default=None, ge=0, le=9),
    scholarships_available: bool | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> UniversitySearchResult:
    from decimal import Decimal

    filters = UniversityFilterRequest(
        country=country,
        city=city,
        major=major,
        min_ranking=min_ranking,
        max_ranking=max_ranking,
        max_tuition=Decimal(str(max_tuition)) if max_tuition is not None else None,
        min_tuition=Decimal(str(min_tuition)) if min_tuition is not None else None,
        max_gpa_required=Decimal(str(max_gpa_required)) if max_gpa_required is not None else None,
        min_gpa_required=Decimal(str(min_gpa_required)) if min_gpa_required is not None else None,
        max_ielts_required=Decimal(str(max_ielts_required)) if max_ielts_required is not None else None,
        scholarships_available=scholarships_available,
        skip=skip,
        limit=limit,
    )
    service = UniversityDiscoveryService(db)
    return await service.filter_universities(filters)


@router.post("/search", response_model=UniversitySearchResult)
async def search_universities(
    request: UniversitySearchRequest,
    db: AsyncSession = Depends(get_db),
) -> UniversitySearchResult:
    service = UniversityDiscoveryService(db)
    return await service.keyword_search(request)


@router.post("/semantic-search", response_model=UniversitySearchResult)
async def semantic_search_universities(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> UniversitySearchResult:
    service = UniversityDiscoveryService(db)
    return await service.semantic_search(request)


@router.get("", response_model=PaginatedResponse[UniversityResponse])
async def list_universities(
    country: str | None = Query(default=None),
    q: str | None = Query(default=None, description="Search by name or city"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UniversityResponse]:
    service = UniversityService(db)
    return await service.search_universities(
        country=country,
        query=q,
        skip=skip,
        limit=limit,
    )


@router.get("/{university_id}", response_model=UniversityDetailResponse)
async def get_university(
    university_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> UniversityDetailResponse:
    service = UniversityService(db)
    return await service.get_university(university_id)
