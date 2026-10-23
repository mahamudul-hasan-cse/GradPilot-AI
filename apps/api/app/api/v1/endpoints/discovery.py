from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.discovery import RecommendUniversitiesRequest, RecommendUniversitiesResponse
from app.services.university_discovery import UniversityDiscoveryService

router = APIRouter(tags=["University Discovery"])


# `/recommend-universities` is the documented path (docs/UNIVERSITY_DISCOVERY.md);
# `/discovery/recommend-universities` is the namespaced alias.
@router.post("/discovery/recommend-universities", response_model=RecommendUniversitiesResponse)
@router.post("/recommend-universities", response_model=RecommendUniversitiesResponse)
async def recommend_universities(
    request: RecommendUniversitiesRequest,
    db: AsyncSession = Depends(get_db),
) -> RecommendUniversitiesResponse:
    """
  Recommend universities categorized as **Safe**, **Target**, and **Ambitious**
  based on GPA, IELTS, budget, country preference, and major.

  Ranking factors:
  - GPA Match (25%)
  - IELTS Match (20%)
  - Budget Match (25%)
  - Ranking Preference (20%)
  - Scholarship Availability (10%)
    """
    service = UniversityDiscoveryService(db)
    return await service.recommend(request)
