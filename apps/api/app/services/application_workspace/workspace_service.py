"""Application Workspace Service — central orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import (
    APPLICATION_STATUSES,
    DEADLINE_TYPES,
    DOCUMENT_TYPES,
    Application,
    ApplicationDeadline,
    ApplicationDocument,
    ApplicationNote,
    ApplicationTask,
)
from app.models.user import User
from app.repositories.application import ApplicationRepository
from app.repositories.application_activity import ApplicationActivityRepository
from app.repositories.application_deadline import ApplicationDeadlineRepository
from app.repositories.application_document import ApplicationDocumentRepository
from app.repositories.application_note import ApplicationNoteRepository
from app.repositories.application_task import ApplicationTaskRepository
from app.repositories.student_profile import StudentProfileRepository
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
    TimelineEventResponse,
)
from app.services.application_workspace.activity_service import ActivityService
from app.services.application_workspace.analytics_service import ApplicationAnalyticsService
from app.services.application_workspace.deadline_engine import DeadlineEngine
from app.services.application_workspace.progress_engine import ProgressEngine
from app.services.application_workspace.task_engine import TaskEngine


class ApplicationWorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.app_repo = ApplicationRepository(db)
        self.doc_repo = ApplicationDocumentRepository(db)
        self.task_repo = ApplicationTaskRepository(db)
        self.note_repo = ApplicationNoteRepository(db)
        self.activity_repo = ApplicationActivityRepository(db)
        self.deadline_repo = ApplicationDeadlineRepository(db)
        self.profile_repo = StudentProfileRepository(db)
        self.progress_engine = ProgressEngine()
        self.task_engine = TaskEngine(db)
        self.deadline_engine = DeadlineEngine(db)
        self.activity_service = ActivityService(db)
        self.analytics_service = ApplicationAnalyticsService(db)

    async def _get_app(self, user: User, application_id: UUID) -> Application:
        app = await self.app_repo.get_by_id_for_user(application_id, user.id)
        if app is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        return app

    async def list_applications(self, user: User, *, skip: int = 0, limit: int = 50) -> list[ApplicationResponse]:
        apps = await self.app_repo.get_by_user_id(user.id, skip=skip, limit=limit)
        return [self._to_response(a) for a in apps]

    async def get_workspace(self, user: User, application_id: UUID) -> ApplicationWorkspaceResponse:
        app = await self._get_app(user, application_id)
        progress = self.progress_engine.apply_to_application(app)
        await self.app_repo.update(app)
        return ApplicationWorkspaceResponse(
            application=self._to_response(app),
            progress=ApplicationProgressResponse(**progress),
            documents=[ApplicationDocumentResponse.model_validate(d) for d in app.documents or []],
            tasks=[ApplicationTaskResponse.model_validate(t) for t in app.tasks or []],
            notes=[ApplicationNoteResponse.model_validate(n) for n in app.workspace_notes or []],
            deadlines=[ApplicationDeadlineResponse.model_validate(d) for d in app.deadlines or []],
            timeline=await self.get_timeline(user, application_id),
        )

    async def create_application(self, user: User, data: ApplicationCreate) -> ApplicationResponse:
        if data.status and data.status not in APPLICATION_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status: {data.status}")

        profile = await self.profile_repo.get_by_user_id(user.id)
        app = Application(
            user_id=user.id,
            title=data.title,
            university_id=data.university_id,
            program_id=data.program_id,
            scholarship_id=data.scholarship_id,
            status=data.status or "planning",
            intake_term=data.intake_term,
            deadline=data.deadline,
            notes=data.notes,
            profile_complete=profile is not None,
        )
        if app.status == "submitted":
            app.submitted_at = datetime.now(UTC)

        created = await self.app_repo.create(app)
        await self.task_engine.generate_tasks(created, due_date=data.deadline)
        await self.deadline_engine.seed_default_deadlines(created)
        created = await self.app_repo.get_by_id_for_user(created.id, user.id)
        self.progress_engine.apply_to_application(created)
        await self.app_repo.update(created)

        await self.activity_service.log(
            application_id=created.id,
            user_id=user.id,
            event_type="application_created",
            title="Application created",
            description=f"Started application workspace{f' for {data.title}' if data.title else ''}.",
        )
        return self._to_response(created)

    async def update_application(
        self, user: User, application_id: UUID, data: ApplicationUpdate
    ) -> ApplicationResponse:
        app = await self._get_app(user, application_id)
        old_status = app.status
        update_data = data.model_dump(exclude_unset=True)

        if "status" in update_data and update_data["status"] not in APPLICATION_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update_data['status']}")

        for field, value in update_data.items():
            setattr(app, field, value)

        if app.status == "submitted" and app.submitted_at is None:
            app.submitted_at = datetime.now(UTC)

        self.progress_engine.apply_to_application(app)
        updated = await self.app_repo.update(app)

        if old_status != app.status:
            await self.activity_service.log(
                application_id=app.id,
                user_id=user.id,
                event_type="status_changed",
                title=f"Status changed to {app.status}",
                metadata={"from": old_status, "to": app.status},
            )
        return self._to_response(updated)

    async def delete_application(self, user: User, application_id: UUID) -> None:
        app = await self._get_app(user, application_id)
        await self.app_repo.delete(app)

    async def get_progress(self, user: User, application_id: UUID) -> ApplicationProgressResponse:
        app = await self._get_app(user, application_id)
        progress = self.progress_engine.apply_to_application(app)
        await self.app_repo.update(app)
        return ApplicationProgressResponse(**progress)

    # Documents
    async def list_documents(self, user: User, application_id: UUID) -> list[ApplicationDocumentResponse]:
        await self._get_app(user, application_id)
        docs = await self.doc_repo.get_by_application(application_id)
        return [ApplicationDocumentResponse.model_validate(d) for d in docs]

    async def add_document(
        self, user: User, application_id: UUID, data: ApplicationDocumentCreate
    ) -> ApplicationDocumentResponse:
        app = await self._get_app(user, application_id)
        if data.document_type not in DOCUMENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid document type: {data.document_type}")

        doc = ApplicationDocument(
            application_id=application_id,
            document_type=data.document_type,
            title=data.title,
            file_name=data.file_name,
            file_url=data.file_url,
            status=data.status or ("uploaded" if data.file_url else "pending"),
            notes=data.notes,
            uploaded_at=datetime.now(UTC) if data.file_url else None,
        )
        created = await self.doc_repo.create(doc)
        app = await self._get_app(user, application_id)
        self.progress_engine.apply_to_application(app)
        await self.app_repo.update(app)

        await self.activity_service.log(
            application_id=application_id,
            user_id=user.id,
            event_type="document_uploaded",
            title=f"{data.title} uploaded",
            description=f"Document type: {data.document_type}",
            metadata={"document_id": str(created.id), "document_type": data.document_type},
        )
        return ApplicationDocumentResponse.model_validate(created)

    async def update_document(
        self, user: User, application_id: UUID, document_id: UUID, data: ApplicationDocumentUpdate
    ) -> ApplicationDocumentResponse:
        await self._get_app(user, application_id)
        doc = await self.doc_repo.get_for_application(document_id, application_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(doc, field, value)
        if data.file_url and doc.uploaded_at is None:
            doc.uploaded_at = datetime.now(UTC)
            doc.status = "uploaded"

        updated = await self.doc_repo.update(doc)
        app = await self._get_app(user, application_id)
        self.progress_engine.apply_to_application(app)
        await self.app_repo.update(app)
        return ApplicationDocumentResponse.model_validate(updated)

    async def delete_document(self, user: User, application_id: UUID, document_id: UUID) -> None:
        await self._get_app(user, application_id)
        doc = await self.doc_repo.get_for_application(document_id, application_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")
        await self.doc_repo.delete(doc)
        app = await self._get_app(user, application_id)
        self.progress_engine.apply_to_application(app)
        await self.app_repo.update(app)

    # Tasks
    async def list_tasks(self, user: User, application_id: UUID) -> list[ApplicationTaskResponse]:
        await self._get_app(user, application_id)
        tasks = await self.task_repo.get_by_application(application_id)
        return [ApplicationTaskResponse.model_validate(t) for t in tasks]

    async def generate_tasks(self, user: User, application_id: UUID) -> list[ApplicationTaskResponse]:
        app = await self._get_app(user, application_id)
        created = await self.task_engine.generate_tasks(app)
        await self.activity_service.log(
            application_id=application_id,
            user_id=user.id,
            event_type="tasks_generated",
            title="Tasks generated",
            description=f"Generated {len(created)} application tasks.",
        )
        return [ApplicationTaskResponse.model_validate(t) for t in created]

    async def add_task(
        self, user: User, application_id: UUID, data: ApplicationTaskCreate
    ) -> ApplicationTaskResponse:
        await self._get_app(user, application_id)
        task = ApplicationTask(application_id=application_id, **data.model_dump())
        created = await self.task_repo.create(task)
        return ApplicationTaskResponse.model_validate(created)

    async def update_task(
        self, user: User, application_id: UUID, task_id: UUID, data: ApplicationTaskUpdate
    ) -> ApplicationTaskResponse:
        await self._get_app(user, application_id)
        task = await self.task_repo.get_for_application(task_id, application_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        if data.status == "completed":
            task = await self.task_engine.complete_task(task)
            await self.activity_service.log(
                application_id=application_id,
                user_id=user.id,
                event_type="task_completed",
                title=f"Task completed: {task.title}",
            )
        else:
            task = await self.task_repo.update(task)
        return ApplicationTaskResponse.model_validate(task)

    async def delete_task(self, user: User, application_id: UUID, task_id: UUID) -> None:
        await self._get_app(user, application_id)
        task = await self.task_repo.get_for_application(task_id, application_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        await self.task_repo.delete(task)

    # Notes
    async def list_notes(self, user: User, application_id: UUID) -> list[ApplicationNoteResponse]:
        await self._get_app(user, application_id)
        notes = await self.note_repo.get_by_application(application_id)
        return [ApplicationNoteResponse.model_validate(n) for n in notes]

    async def add_note(
        self, user: User, application_id: UUID, data: ApplicationNoteCreate
    ) -> ApplicationNoteResponse:
        await self._get_app(user, application_id)
        note = ApplicationNote(application_id=application_id, **data.model_dump())
        created = await self.note_repo.create(note)
        return ApplicationNoteResponse.model_validate(created)

    async def update_note(
        self, user: User, application_id: UUID, note_id: UUID, data: ApplicationNoteUpdate
    ) -> ApplicationNoteResponse:
        await self._get_app(user, application_id)
        note = await self.note_repo.get_for_application(note_id, application_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Note not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(note, field, value)
        updated = await self.note_repo.update(note)
        return ApplicationNoteResponse.model_validate(updated)

    async def delete_note(self, user: User, application_id: UUID, note_id: UUID) -> None:
        await self._get_app(user, application_id)
        note = await self.note_repo.get_for_application(note_id, application_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Note not found")
        await self.note_repo.delete(note)

    # Deadlines
    async def list_deadlines(self, user: User, application_id: UUID) -> list[ApplicationDeadlineResponse]:
        await self._get_app(user, application_id)
        deadlines = await self.deadline_repo.get_by_application(application_id)
        return [ApplicationDeadlineResponse.model_validate(d) for d in deadlines]

    async def add_deadline(
        self, user: User, application_id: UUID, data: ApplicationDeadlineCreate
    ) -> ApplicationDeadlineResponse:
        await self._get_app(user, application_id)
        if data.deadline_type not in DEADLINE_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid deadline type: {data.deadline_type}")
        deadline = ApplicationDeadline(application_id=application_id, **data.model_dump())
        created = await self.deadline_repo.create(deadline)
        return ApplicationDeadlineResponse.model_validate(created)

    async def update_deadline(
        self, user: User, application_id: UUID, deadline_id: UUID, data: ApplicationDeadlineUpdate
    ) -> ApplicationDeadlineResponse:
        await self._get_app(user, application_id)
        deadline = await self.deadline_repo.get_for_application(deadline_id, application_id)
        if deadline is None:
            raise HTTPException(status_code=404, detail="Deadline not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(deadline, field, value)
        updated = await self.deadline_repo.update(deadline)
        return ApplicationDeadlineResponse.model_validate(updated)

    async def delete_deadline(self, user: User, application_id: UUID, deadline_id: UUID) -> None:
        await self._get_app(user, application_id)
        deadline = await self.deadline_repo.get_for_application(deadline_id, application_id)
        if deadline is None:
            raise HTTPException(status_code=404, detail="Deadline not found")
        await self.deadline_repo.delete(deadline)

    async def get_timeline(self, user: User, application_id: UUID) -> ApplicationTimelineResponse:
        await self._get_app(user, application_id)
        events = await self.activity_repo.get_timeline(application_id)
        return ApplicationTimelineResponse(
            events=[
                TimelineEventResponse(
                    id=e.id,
                    event_type=e.event_type,
                    title=e.title,
                    description=e.description,
                    metadata=e.event_metadata,
                    created_at=e.created_at,
                )
                for e in events
            ],
            total=len(events),
        )

    async def get_analytics(self) -> ApplicationAnalyticsResponse:
        data = await self.analytics_service.get_dashboard()
        return ApplicationAnalyticsResponse(**data)

    async def process_reminders(self) -> list[dict]:
        pending = await self.deadline_engine.get_pending_reminders()
        sent = []
        for deadline in pending:
            if self.deadline_engine.should_send_reminder(deadline):
                await self.deadline_engine.mark_reminder_sent(deadline)
                sent.append({
                    "deadline_id": str(deadline.id),
                    "application_id": str(deadline.application_id),
                    "title": deadline.title,
                    "due_date": deadline.due_date.isoformat(),
                })
        return sent

    def _to_response(self, app: Application) -> ApplicationResponse:
        return ApplicationResponse.model_validate(app)
