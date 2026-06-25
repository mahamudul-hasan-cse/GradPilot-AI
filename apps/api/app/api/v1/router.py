from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    applications,
    auth,
    discovery,
    documents,
    ingestion,
    profile,
    recommendations,
    scholarships,
    student,
    universities,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(ai.router)
api_router.include_router(student.router)
api_router.include_router(documents.router)
api_router.include_router(universities.router)
api_router.include_router(discovery.router)
api_router.include_router(recommendations.router)
api_router.include_router(ingestion.router)
api_router.include_router(scholarships.router)
api_router.include_router(applications.router)
