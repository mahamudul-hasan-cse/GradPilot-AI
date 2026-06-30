"""SOP Studio REST API — rich-text SOP authoring with AI assistance."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.sop_studio import (
    SOPAIActionResponse,
    SOPAutosaveRequest,
    SOPCollaborationJoinRequest,
    SOPCollaborationSessionResponse,
    SOPCommentCreate,
    SOPCommentResponse,
    SOPDocumentCreate,
    SOPDocumentResponse,
    SOPDocumentUpdate,
    SOPDraftRequest,
    SOPExportResponse,
    SOPGrammarRequest,
    SOPGrammarResponse,
    SOPHistoryResponse,
    SOPPlagiarismResponse,
    SOPRewriteRequest,
    SOPScoreBreakdown,
    SOPScoreRequest,
    SOPStudioAnalyticsResponse,
    SOPTailorScholarshipRequest,
    SOPTailorUniversityRequest,
    SOPVersionCompareResponse,
    SOPVersionResponse,
)
from app.services.sop_studio.service import SOPStudioService

router = APIRouter(prefix="/sop-studio", tags=["SOP Studio"])


@router.get("/documents", response_model=list[SOPDocumentResponse])
async def list_sop_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[SOPDocumentResponse]:
    """List all SOP documents for the authenticated user (supports multiple SOPs)."""
    service = SOPStudioService(db)
    return await service.list_documents(current_user.id, skip=skip, limit=limit)


@router.post("/documents", response_model=SOPDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_sop_document(
    data: SOPDocumentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPDocumentResponse:
    """
    Create a new SOP document.

    Optionally provide `initial_content` for the rich-text editor. Links to applications,
    universities, or scholarships for tailoring context.
    """
    service = SOPStudioService(db)
    return await service.create_document(current_user, data)


@router.get("/analytics", response_model=SOPStudioAnalyticsResponse)
async def get_sop_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPStudioAnalyticsResponse:
    """Aggregate SOP Studio usage analytics for the current user."""
    service = SOPStudioService(db)
    return await service.analytics(current_user.id)


@router.get("/documents/{document_id}", response_model=SOPDocumentResponse)
async def get_sop_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPDocumentResponse:
    """Get a single SOP with current rich-text content (HTML + plain)."""
    service = SOPStudioService(db)
    return await service.get_document(current_user.id, document_id)


@router.patch("/documents/{document_id}", response_model=SOPDocumentResponse)
async def update_sop_document(
    document_id: UUID,
    data: SOPDocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPDocumentResponse:
    """Update SOP metadata (title, status, target word count, university/scholarship names)."""
    service = SOPStudioService(db)
    return await service.update_document(current_user.id, document_id, data)


@router.delete("/documents/{document_id}", response_model=MessageResponse)
async def delete_sop_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Delete an SOP document and all versions, comments, and history."""
    service = SOPStudioService(db)
    await service.delete_document(current_user.id, document_id)
    return MessageResponse(message="SOP document deleted")


@router.post("/documents/{document_id}/autosave", response_model=SOPDocumentResponse)
async def autosave_sop(
    document_id: UUID,
    data: SOPAutosaveRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPDocumentResponse:
    """
    Autosave rich-text editor content.

    Accepts `content_html` from the editor; `content_plain` is derived if omitted.
    Creates an autosave version snapshot in version history.
    """
    service = SOPStudioService(db)
    return await service.autosave(current_user.id, document_id, data)


@router.get("/documents/{document_id}/word-count")
async def get_word_count(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Word counter with target comparison."""
    service = SOPStudioService(db)
    return await service.word_count(current_user.id, document_id)


@router.post("/documents/{document_id}/ai/draft", response_model=SOPAIActionResponse)
async def ai_draft_sop(
    document_id: UUID,
    request: SOPDraftRequest | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPAIActionResponse:
    """
    **AI Draft** — generate a full SOP from the Student Digital Twin profile.

    Uses academic profile, achievements, goals, and target university/scholarship context.
    Returns content with an explainable `reason`.
    """
    service = SOPStudioService(db)
    return await service.ai_draft(current_user, document_id, request or SOPDraftRequest())


@router.post("/documents/{document_id}/ai/rewrite", response_model=SOPAIActionResponse)
async def ai_rewrite_sop(
    document_id: UUID,
    request: SOPRewriteRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPAIActionResponse:
    """**AI Rewrite** — improve clarity, tone, or a specific section per instruction."""
    service = SOPStudioService(db)
    return await service.ai_rewrite(current_user.id, document_id, request)


@router.post("/documents/{document_id}/ai/grammar", response_model=SOPGrammarResponse)
async def grammar_review_sop(
    document_id: UUID,
    request: SOPGrammarRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPGrammarResponse:
    """**Grammar Review** — rule-based checks with optional LLM polish."""
    service = SOPStudioService(db)
    return await service.grammar_review(current_user.id, document_id, request)


@router.post("/documents/{document_id}/ai/tailor/university", response_model=SOPAIActionResponse)
async def tailor_university_sop(
    document_id: UUID,
    request: SOPTailorUniversityRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPAIActionResponse:
    """**University-specific tailoring** — adapt SOP for a target program."""
    service = SOPStudioService(db)
    return await service.tailor_university(current_user.id, document_id, request)


@router.post("/documents/{document_id}/ai/tailor/scholarship", response_model=SOPAIActionResponse)
async def tailor_scholarship_sop(
    document_id: UUID,
    request: SOPTailorScholarshipRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPAIActionResponse:
    """**Scholarship-specific tailoring** — adapt SOP for a funding application."""
    service = SOPStudioService(db)
    return await service.tailor_scholarship(current_user.id, document_id, request)


@router.post("/documents/{document_id}/ai/score", response_model=SOPScoreBreakdown)
async def score_sop(
    document_id: UUID,
    request: SOPScoreRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPScoreBreakdown:
    """
    **AI Scoring** — clarity, structure, uniqueness, program fit, and overall score.

    Includes actionable feedback and per-dimension reasons.
    """
    service = SOPStudioService(db)
    return await service.score_document(current_user.id, document_id, request)


@router.post("/documents/{document_id}/plagiarism", response_model=SOPPlagiarismResponse)
async def plagiarism_check_sop(
    document_id: UUID,
    request: SOPScoreRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPPlagiarismResponse:
    """**Plagiarism placeholder** — records check request; connect external provider for real scans."""
    service = SOPStudioService(db)
    return await service.plagiarism_check(current_user.id, document_id, request)


@router.post("/documents/{document_id}/export", response_model=SOPExportResponse)
async def export_sop(
    document_id: UUID,
    export_format: str = Query(..., alias="format", pattern="^(pdf|docx|markdown)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPExportResponse:
    """Export SOP as **PDF**, **DOCX**, or **Markdown**."""
    service = SOPStudioService(db)
    return await service.export_document(current_user.id, document_id, export_format=export_format)


@router.get("/documents/{document_id}/versions", response_model=list[SOPVersionResponse])
async def list_versions(
    document_id: UUID,
    include_autosave: bool = Query(default=False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[SOPVersionResponse]:
    """**Version history** — list saved versions (autosave snapshots optional)."""
    service = SOPStudioService(db)
    return await service.list_versions(current_user.id, document_id, include_autosave=include_autosave)


@router.get("/documents/{document_id}/versions/compare", response_model=SOPVersionCompareResponse)
async def compare_versions(
    document_id: UUID,
    version_a: UUID = Query(...),
    version_b: UUID = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPVersionCompareResponse:
    """**Version comparison** — similarity, word delta, and diff summary."""
    service = SOPStudioService(db)
    return await service.compare_versions(current_user.id, document_id, version_a, version_b)


@router.get("/documents/{document_id}/versions/{version_id}", response_model=SOPVersionResponse)
async def get_version(
    document_id: UUID,
    version_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPVersionResponse:
    """Get a specific version snapshot."""
    service = SOPStudioService(db)
    return await service.get_version(current_user.id, document_id, version_id)


@router.get("/documents/{document_id}/comments", response_model=list[SOPCommentResponse])
async def list_comments(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[SOPCommentResponse]:
    """List reviewer **comments** on an SOP."""
    service = SOPStudioService(db)
    return await service.list_comments(current_user.id, document_id)


@router.post("/documents/{document_id}/comments", response_model=SOPCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    document_id: UUID,
    data: SOPCommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPCommentResponse:
    """Add a comment with optional anchor text and version reference."""
    service = SOPStudioService(db)
    return await service.add_comment(current_user, document_id, data)


@router.post("/documents/{document_id}/comments/{comment_id}/resolve", response_model=SOPCommentResponse)
async def resolve_comment(
    document_id: UUID,
    comment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPCommentResponse:
    """Mark a comment as resolved."""
    service = SOPStudioService(db)
    return await service.resolve_comment(current_user.id, document_id, comment_id)


@router.get("/documents/{document_id}/history", response_model=list[SOPHistoryResponse])
async def list_history(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[SOPHistoryResponse]:
    """Audit **history** of actions (draft, rewrite, export, autosave, etc.)."""
    service = SOPStudioService(db)
    return await service.list_history(current_user.id, document_id)


@router.post(
    "/documents/{document_id}/collaboration/join",
    response_model=SOPCollaborationSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def join_collaboration(
    document_id: UUID,
    data: SOPCollaborationJoinRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPCollaborationSessionResponse:
    """
    Join a **collaborative editing** session.

    Architecture supports multi-user sessions with roles (editor, reviewer, viewer).
    Use the returned `session_token` for heartbeat updates.
    """
    service = SOPStudioService(db)
    return await service.join_collaboration(current_user, document_id, data)


@router.get("/documents/{document_id}/collaboration/sessions", response_model=list[SOPCollaborationSessionResponse])
async def list_collaboration_sessions(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[SOPCollaborationSessionResponse]:
    """List active collaboration sessions for an SOP."""
    service = SOPStudioService(db)
    return await service.list_collaboration_sessions(current_user.id, document_id)


@router.post("/documents/{document_id}/collaboration/heartbeat", response_model=SOPCollaborationSessionResponse)
async def collaboration_heartbeat(
    document_id: UUID,
    session_token: str = Query(...),
    cursor_position: int | None = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SOPCollaborationSessionResponse:
    """Update collaboration session presence and optional cursor position."""
    service = SOPStudioService(db)
    return await service.collaboration_heartbeat(
        current_user.id, document_id, session_token, cursor_position=cursor_position
    )
