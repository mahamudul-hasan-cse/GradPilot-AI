from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.scholarship import ScholarshipResponse
from app.schemas.university import ProgramResponse, UniversityResponse


class ProgressBreakdownItem(BaseModel):
    label: str
    weight: int
    completed: bool
    percent: int


class ApplicationProgressResponse(BaseModel):
    progress_percent: float
    breakdown: dict[str, ProgressBreakdownItem]


class ApplicationCreate(BaseModel):
    university_id: UUID | None = None
    program_id: UUID | None = None
    scholarship_id: UUID | None = None
    title: str | None = Field(default=None, max_length=255)
    status: str = Field(default="planning")
    intake_term: str | None = Field(default=None, max_length=50)
    notes: str | None = None
    deadline: date | None = None


class ApplicationUpdate(BaseModel):
    university_id: UUID | None = None
    program_id: UUID | None = None
    scholarship_id: UUID | None = None
    title: str | None = None
    status: str | None = None
    intake_term: str | None = None
    notes: str | None = None
    deadline: date | None = None
    profile_complete: bool | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    program_id: UUID | None
    university_id: UUID | None
    scholarship_id: UUID | None
    title: str | None
    status: str
    intake_term: str | None
    notes: str | None
    submitted_at: datetime | None
    deadline: date | None
    progress_percent: float
    progress_breakdown: dict[str, Any] | None
    profile_complete: bool
    documents_complete: bool
    sop_complete: bool
    lor_complete: bool
    submitted_complete: bool
    created_at: datetime
    updated_at: datetime
    program: ProgramResponse | None = None
    university: UniversityResponse | None = None
    scholarship: ScholarshipResponse | None = None


class ApplicationDocumentCreate(BaseModel):
    document_type: str
    title: str = Field(min_length=1, max_length=255)
    file_name: str | None = None
    file_url: str | None = None
    status: str | None = None
    notes: str | None = None


class ApplicationDocumentUpdate(BaseModel):
    title: str | None = None
    file_name: str | None = None
    file_url: str | None = None
    status: str | None = None
    notes: str | None = None


class ApplicationDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    document_type: str
    title: str
    file_name: str | None
    file_url: str | None
    status: str
    notes: str | None
    uploaded_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApplicationTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    task_type: str = Field(default="custom")
    status: str = Field(default="pending")
    priority: str = Field(default="medium")
    due_date: date | None = None
    sort_order: int = 0


class ApplicationTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: date | None = None
    sort_order: int | None = None


class ApplicationTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    title: str
    description: str | None
    task_type: str
    status: str
    priority: str
    due_date: date | None
    completed_at: datetime | None
    is_auto_generated: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ApplicationNoteCreate(BaseModel):
    title: str | None = None
    content: str = Field(min_length=1)
    is_pinned: bool = False


class ApplicationNoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    is_pinned: bool | None = None


class ApplicationNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    title: str | None
    content: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime


class ApplicationDeadlineCreate(BaseModel):
    deadline_type: str
    title: str = Field(min_length=1, max_length=255)
    due_date: date
    reminder_days_before: int = Field(default=7, ge=1, le=90)
    notes: str | None = None


class ApplicationDeadlineUpdate(BaseModel):
    title: str | None = None
    due_date: date | None = None
    reminder_days_before: int | None = None
    is_completed: bool | None = None
    notes: str | None = None


class ApplicationDeadlineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    deadline_type: str
    title: str
    due_date: date
    reminder_days_before: int
    reminder_sent_at: datetime | None
    is_completed: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class TimelineEventResponse(BaseModel):
    id: UUID
    event_type: str
    title: str
    description: str | None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class ApplicationTimelineResponse(BaseModel):
    events: list[TimelineEventResponse]
    total: int


class ApplicationWorkspaceResponse(BaseModel):
    application: ApplicationResponse
    progress: ApplicationProgressResponse
    documents: list[ApplicationDocumentResponse]
    tasks: list[ApplicationTaskResponse]
    notes: list[ApplicationNoteResponse]
    deadlines: list[ApplicationDeadlineResponse]
    timeline: ApplicationTimelineResponse


class ApplicationAnalyticsResponse(BaseModel):
    total_applications: int
    status_distribution: dict[str, int]
    acceptance_rate: float
    completion_rate: float
    country_distribution: dict[str, int] = Field(default_factory=dict)
    university_distribution: dict[str, int] = Field(default_factory=dict)
    upcoming_deadlines: int
    recent_applications: list[dict[str, Any]]
