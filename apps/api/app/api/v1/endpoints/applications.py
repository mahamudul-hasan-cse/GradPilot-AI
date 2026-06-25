from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.application_workspace import (
    ApplicationAnalyticsResponse,
    ApplicationCreate,
    ApplicationDeadlineCreate,
    ApplicationDeadlineResponse,
    ApplicationDeadlineUpdate,
    ApplicationDocumentCreate,
    ApplicationDocumentResponse,
    ApplicationDocumentUpdate,
    ApplicationNoteCreate,
    ApplicationNoteResponse,
    ApplicationNoteUpdate,
    ApplicationProgressResponse,
    ApplicationResponse,
    ApplicationTaskCreate,
    ApplicationTaskResponse,
    ApplicationTaskUpdate,
    ApplicationTimelineResponse,
    ApplicationUpdate,
    ApplicationWorkspaceResponse,
)
from app.schemas.common import MessageResponse
from app.services.application_workspace.workspace_service import ApplicationWorkspaceService

router = APIRouter(prefix="/applications", tags=["Application Workspace"])


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationResponse]:
    """List all applications for the authenticated user."""
    service = ApplicationWorkspaceService(db)
    return await service.list_applications(current_user, skip=skip, limit=limit)


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """
    Create a new application workspace.

    Automatically generates tasks, deadlines, and activity timeline entry.
    Initial status: **planning**.
    """
    service = ApplicationWorkspaceService(db)
    return await service.create_application(current_user, data)


@router.get("/analytics", response_model=ApplicationAnalyticsResponse)
async def get_application_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApplicationAnalyticsResponse:
    """
    Admin dashboard metrics: total applications, acceptance rate,
    country distribution, completion rate, and upcoming deadlines.
    """
    service = ApplicationWorkspaceService(db)
    return await service.get_analytics()


@router.post("/reminders/process")
async def process_deadline_reminders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Process pending deadline reminders (admin/cron endpoint)."""
    service = ApplicationWorkspaceService(db)
    sent = await service.process_reminders()
    return {"reminders_sent": len(sent), "details": sent}


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    service = ApplicationWorkspaceService(db)
    workspace = await service.get_workspace(current_user, application_id)
    return workspace.application


@router.get("/{application_id}/workspace", response_model=ApplicationWorkspaceResponse)
async def get_application_workspace(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationWorkspaceResponse:
    """
    Full application workspace: application, progress bar, documents,
    tasks, notes, deadlines, and activity timeline.
    """
    service = ApplicationWorkspaceService(db)
    return await service.get_workspace(current_user, application_id)


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: UUID,
    data: ApplicationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """
    Update application. Status values:

    `planning` | `preparing` | `ready` | `submitted` | `interview` |
    `accepted` | `rejected` | `deferred` | `withdrawn`
    """
    service = ApplicationWorkspaceService(db)
    return await service.update_application(current_user, application_id, data)


@router.delete("/{application_id}", response_model=MessageResponse)
async def delete_application(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = ApplicationWorkspaceService(db)
    await service.delete_application(current_user, application_id)
    return MessageResponse(message="Application deleted")


@router.get("/{application_id}/progress", response_model=ApplicationProgressResponse)
async def get_application_progress(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationProgressResponse:
    """
    Calculate application completion progress.

    | Component | Weight |
    |-----------|--------|
    | Profile Complete | 20% |
    | Documents | 30% |
    | SOP | 15% |
    | Recommendation Letter | 15% |
    | Application Submitted | 20% |
    """
    service = ApplicationWorkspaceService(db)
    return await service.get_progress(current_user, application_id)


# Documents
@router.get("/{application_id}/documents", response_model=list[ApplicationDocumentResponse])
async def list_documents(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationDocumentResponse]:
    service = ApplicationWorkspaceService(db)
    return await service.list_documents(current_user, application_id)


@router.post(
    "/{application_id}/documents",
    response_model=ApplicationDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_document(
    application_id: UUID,
    data: ApplicationDocumentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationDocumentResponse:
    service = ApplicationWorkspaceService(db)
    return await service.add_document(current_user, application_id, data)


@router.patch("/{application_id}/documents/{document_id}", response_model=ApplicationDocumentResponse)
async def update_document(
    application_id: UUID,
    document_id: UUID,
    data: ApplicationDocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationDocumentResponse:
    service = ApplicationWorkspaceService(db)
    return await service.update_document(current_user, application_id, document_id, data)


@router.delete("/{application_id}/documents/{document_id}", response_model=MessageResponse)
async def delete_document(
    application_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = ApplicationWorkspaceService(db)
    await service.delete_document(current_user, application_id, document_id)
    return MessageResponse(message="Document deleted")


# Tasks
@router.get("/{application_id}/tasks", response_model=list[ApplicationTaskResponse])
async def list_tasks(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationTaskResponse]:
    service = ApplicationWorkspaceService(db)
    return await service.list_tasks(current_user, application_id)


@router.post("/{application_id}/tasks/generate", response_model=list[ApplicationTaskResponse])
async def generate_tasks(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationTaskResponse]:
    """Generate intelligent default tasks (transcript, SOP, LOR, fee, submit, visa)."""
    service = ApplicationWorkspaceService(db)
    return await service.generate_tasks(current_user, application_id)


@router.post(
    "/{application_id}/tasks",
    response_model=ApplicationTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_task(
    application_id: UUID,
    data: ApplicationTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationTaskResponse:
    service = ApplicationWorkspaceService(db)
    return await service.add_task(current_user, application_id, data)


@router.patch("/{application_id}/tasks/{task_id}", response_model=ApplicationTaskResponse)
async def update_task(
    application_id: UUID,
    task_id: UUID,
    data: ApplicationTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationTaskResponse:
    service = ApplicationWorkspaceService(db)
    return await service.update_task(current_user, application_id, task_id, data)


@router.delete("/{application_id}/tasks/{task_id}", response_model=MessageResponse)
async def delete_task(
    application_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = ApplicationWorkspaceService(db)
    await service.delete_task(current_user, application_id, task_id)
    return MessageResponse(message="Task deleted")


# Notes
@router.get("/{application_id}/notes", response_model=list[ApplicationNoteResponse])
async def list_notes(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationNoteResponse]:
    service = ApplicationWorkspaceService(db)
    return await service.list_notes(current_user, application_id)


@router.post(
    "/{application_id}/notes",
    response_model=ApplicationNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_note(
    application_id: UUID,
    data: ApplicationNoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationNoteResponse:
    service = ApplicationWorkspaceService(db)
    return await service.add_note(current_user, application_id, data)


@router.patch("/{application_id}/notes/{note_id}", response_model=ApplicationNoteResponse)
async def update_note(
    application_id: UUID,
    note_id: UUID,
    data: ApplicationNoteUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationNoteResponse:
    service = ApplicationWorkspaceService(db)
    return await service.update_note(current_user, application_id, note_id, data)


@router.delete("/{application_id}/notes/{note_id}", response_model=MessageResponse)
async def delete_note(
    application_id: UUID,
    note_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = ApplicationWorkspaceService(db)
    await service.delete_note(current_user, application_id, note_id)
    return MessageResponse(message="Note deleted")


# Deadlines
@router.get("/{application_id}/deadlines", response_model=list[ApplicationDeadlineResponse])
async def list_deadlines(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationDeadlineResponse]:
    service = ApplicationWorkspaceService(db)
    return await service.list_deadlines(current_user, application_id)


@router.post(
    "/{application_id}/deadlines",
    response_model=ApplicationDeadlineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_deadline(
    application_id: UUID,
    data: ApplicationDeadlineCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationDeadlineResponse:
    """Add deadline: application, scholarship, interview, visa, or custom."""
    service = ApplicationWorkspaceService(db)
    return await service.add_deadline(current_user, application_id, data)


@router.patch("/{application_id}/deadlines/{deadline_id}", response_model=ApplicationDeadlineResponse)
async def update_deadline(
    application_id: UUID,
    deadline_id: UUID,
    data: ApplicationDeadlineUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationDeadlineResponse:
    service = ApplicationWorkspaceService(db)
    return await service.update_deadline(current_user, application_id, deadline_id, data)


@router.delete("/{application_id}/deadlines/{deadline_id}", response_model=MessageResponse)
async def delete_deadline(
    application_id: UUID,
    deadline_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = ApplicationWorkspaceService(db)
    await service.delete_deadline(current_user, application_id, deadline_id)
    return MessageResponse(message="Deadline deleted")


# Timeline
@router.get("/{application_id}/timeline", response_model=ApplicationTimelineResponse)
async def get_timeline(
    application_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationTimelineResponse:
    """Activity timeline for the application workspace."""
    service = ApplicationWorkspaceService(db)
    return await service.get_timeline(current_user, application_id)

