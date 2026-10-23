from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user_optional, get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.recommendation import (
    UniversityRecommendationRequest,
    UniversityRecommendationResponse,
)
from app.schemas.scholarship_recommendation import (
    ScholarshipRecommendationAnalytics,
    ScholarshipRecommendationRequest,
    ScholarshipRecommendationResponse,
)
from app.services.recommendation.engine import UniversityRecommendationEngine
from app.services.scholarship_recommendation.service import ScholarshipRecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/universities", response_model=UniversityRecommendationResponse)
async def recommend_universities(
    request: UniversityRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_active_user_optional),
) -> UniversityRecommendationResponse:
    """
    Generate personalized university recommendations classified as **Safe**, **Target**, or **Ambitious**.

    ## Scoring (0–100)

    | Factor | Weight |
    |--------|--------|
    | Academic Match (GPA + experience) | 35% |
    | Language Match (IELTS) | 20% |
    | Budget Match | 20% |
    | Program Match | 15% |
    | Scholarship Availability | 10% |

    ## Tier Classification

    - **Safe**: score ≥ 80
    - **Target**: score 60–79
    - **Ambitious**: score < 60
    """
    engine = UniversityRecommendationEngine(db)
    user_id = current_user.id if current_user else None
    return await engine.recommend(request, user_id=user_id)


@router.post("/scholarships", response_model=ScholarshipRecommendationResponse)
async def recommend_scholarships(
    request: ScholarshipRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_active_user_optional),
) -> ScholarshipRecommendationResponse:
    """
    Match students to scholarships and rank by eligibility probability.

    ## Scoring (0–100)

    | Factor | Weight |
    |--------|--------|
    | Academic Match | 30% |
    | Language Match | 20% |
    | Degree Match | 15% |
    | Country Match | 15% |
    | Research Match | 10% |
    | Work Experience Match | 10% |

    ## Match Categories

    | Category | Score |
    |----------|-------|
    | Excellent Match | 90–100 |
    | Strong Match | 75–89 |
    | Possible Match | 60–74 |
    | Low Match | < 60 |

    Returns **scholarship score**, **eligibility probability**, and a human-readable **explanation** per match.
    Results are cached in Redis and stored in recommendation history.
    """
    service = ScholarshipRecommendationService(db)
    user_id = current_user.id if current_user else None
    return await service.recommend(request, user_id=user_id)


@router.get("/scholarships/analytics", response_model=ScholarshipRecommendationAnalytics)
async def get_scholarship_recommendation_analytics(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
) -> ScholarshipRecommendationAnalytics:
    """
    Admin analytics for the scholarship matching engine.

    Returns aggregate metrics: total recommendations, average scores,
    eligibility probability, cache hit rate, match category distribution,
    and recent request history.
    """
    service = ScholarshipRecommendationService(db)
    return await service.get_analytics()
