from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_current_active_user_optional
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile_intelligence import (
    ProfileAnalysisAnalytics,
    ProfileAnalysisRequest,
    ProfileAnalysisResponse,
)
from app.schemas.student_profile import (
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
)
from app.services.profile_intelligence.service import ProfileIntelligenceService
from app.services.student_profile import StudentProfileService

router = APIRouter(prefix="/profile", tags=["Student Profile"])


@router.get("", response_model=StudentProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StudentProfileResponse:
    service = StudentProfileService(db)
    return await service.get_profile(current_user)


@router.post("", response_model=StudentProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: StudentProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StudentProfileResponse:
    service = StudentProfileService(db)
    return await service.create_profile(current_user, data)


@router.put("", response_model=StudentProfileResponse)
async def update_profile(
    data: StudentProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StudentProfileResponse:
    service = StudentProfileService(db)
    return await service.upsert_profile(current_user, data)


@router.post("/analyze", response_model=ProfileAnalysisResponse)
async def analyze_profile(
    request: ProfileAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_active_user_optional),
) -> ProfileAnalysisResponse:
    """
    Analyze a student profile and generate actionable study-abroad guidance.

    ## Outputs

    1. **Admission Readiness Score** (0–100) — academic, language, research, work, completeness
    2. **Scholarship Readiness Score** (0–100) — competitiveness for merit funding
    3. **Employability Score** (0–100) — post-graduation career prospects
    4. **Strengths** — profile highlights
    5. **Weaknesses** — gaps to address
    6. **Missing Requirements** — typical admission gaps
    7. **Recommended Actions** — prioritized improvement steps
    8. **Suggested Countries** — best-fit destinations
    9. **Suggested University Tier** — Top Tier, Competitive, Target, or Foundation/Safety
    10. **Profile Summary** — executive narrative

    Every score includes a human-readable explanation in `score_explanations`.
    Results are cached in Redis and stored in analysis history.
    """
    service = ProfileIntelligenceService(db)
    try:
        user_id = current_user.id if current_user else None
        return await service.analyze(request, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/analyze/analytics", response_model=ProfileAnalysisAnalytics)
async def get_profile_analysis_analytics(
    db: AsyncSession = Depends(get_db),
) -> ProfileAnalysisAnalytics:
    """
    Admin analytics dashboard for the Profile Intelligence Engine.

    Returns aggregate scores, cache hit rate, university tier distribution,
    analyzer usage, and recent analysis history.
    """
    service = ProfileIntelligenceService(db)
    return await service.get_analytics()
