"""Document Intelligence Platform API."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document_intelligence import (
    DocumentJobResponse,
    DocumentUploadResponse,
    DocumentVersionResponse,
    ParseDocumentResponse,
    ValidationResponse,
)
from app.services.document_intelligence.service import DocumentIntelligenceService

router = APIRouter(prefix="/documents", tags=["Document Intelligence"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str | None = Form(default=None),
    application_id: UUID | None = Form(default=None),
    parent_id: UUID | None = Form(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """
    Upload an admission document for intelligent processing.

    Supported types: passport, transcript, degree_certificate, cv, ielts_trf,
    toefl, gre, lor, sop.

    Triggers async pipeline: OCR → classify → extract → validate → twin sync.
    """
    service = DocumentIntelligenceService(db)
    return await service.upload(
        current_user,
        file,
        document_type=document_type,
        application_id=application_id,
        parent_id=parent_id,
        background_tasks=background_tasks,
    )


@router.get("", response_model=list[DocumentUploadResponse])
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentUploadResponse]:
    """List all uploaded documents for the authenticated user."""
    service = DocumentIntelligenceService(db)
    return await service.list_documents(current_user, skip=skip, limit=limit)


@router.get("/jobs/{job_id}", response_model=DocumentJobResponse)
async def get_processing_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentJobResponse:
    """Get async processing job status."""
    service = DocumentIntelligenceService(db)
    return await service.get_job(current_user, job_id)


@router.get("/{document_id}", response_model=DocumentUploadResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """Retrieve document with extraction results and validation status."""
    service = DocumentIntelligenceService(db)
    return await service.get_document(current_user, document_id)


@router.post("/{document_id}/parse", response_model=ParseDocumentResponse)
async def parse_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ParseDocumentResponse:
    """
    Run the full parsing pipeline on an uploaded document.

    Stages: OCR → Classification → Field Extraction → Validation → Confidence Scoring → Twin Sync.
    """
    service = DocumentIntelligenceService(db)
    return await service.parse_document(current_user, document_id)


@router.post("/{document_id}/validate", response_model=ValidationResponse)
async def validate_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ValidationResponse:
    """Re-run validation rules on extracted document fields."""
    service = DocumentIntelligenceService(db)
    return await service.validate_document(current_user, document_id)


@router.get("/{document_id}/versions", response_model=DocumentVersionResponse)
async def get_document_versions(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentVersionResponse:
    """Get version history for a document."""
    service = DocumentIntelligenceService(db)
    return await service.get_versions(current_user, document_id)
