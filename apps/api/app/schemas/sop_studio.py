"""SOP Studio API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SOPDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    target_type: str = Field(default="university", pattern="^(university|scholarship|general)$")
    application_id: UUID | None = None
    university_id: UUID | None = None
    scholarship_id: UUID | None = None
    university_name: str | None = None
    program_name: str | None = None
    scholarship_name: str | None = None
    target_word_count: int = Field(default=750, ge=200, le=2000)
    initial_content: str | None = None


class SOPDocumentUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    university_name: str | None = None
    program_name: str | None = None
    scholarship_name: str | None = None
    target_word_count: int | None = Field(default=None, ge=200, le=2000)


class SOPAutosaveRequest(BaseModel):
    content_html: str
    content_plain: str | None = None
    cursor_position: int | None = None


class SOPDraftRequest(BaseModel):
    prompt: str | None = None
    themes: list[str] = Field(default_factory=list)
    tone: str = Field(default="professional")
    target_word_count: int | None = None


class SOPRewriteRequest(BaseModel):
    content_plain: str
    instruction: str = Field(default="Improve clarity and flow while preserving meaning.")
    section: str | None = None


class SOPGrammarRequest(BaseModel):
    content_plain: str


class SOPTailorUniversityRequest(BaseModel):
    content_plain: str
    university_name: str
    program_name: str
    highlights: list[str] = Field(default_factory=list)


class SOPTailorScholarshipRequest(BaseModel):
    content_plain: str
    scholarship_name: str
    provider: str | None = None
    eligibility_notes: str | None = None


class SOPScoreRequest(BaseModel):
    content_plain: str


class SOPCommentCreate(BaseModel):
    body: str = Field(min_length=1)
    anchor_text: str | None = None
    version_id: UUID | None = None


class SOPCollaborationJoinRequest(BaseModel):
    role: str = Field(default="editor", pattern="^(editor|reviewer|viewer)$")


class SOPVersionResponse(BaseModel):
    id: UUID
    version_number: int
    content_html: str
    content_plain: str
    word_count: int
    change_summary: str | None
    source_action: str
    is_autosave: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SOPCommentResponse(BaseModel):
    id: UUID
    author_name: str
    body: str
    anchor_text: str | None
    is_resolved: bool
    version_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SOPHistoryResponse(BaseModel):
    id: UUID
    action: str
    version_id: UUID | None
    details: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SOPDocumentResponse(BaseModel):
    id: UUID
    title: str
    target_type: str
    status: str
    word_count: int
    target_word_count: int
    university_name: str | None
    program_name: str | None
    scholarship_name: str | None
    application_id: UUID | None
    current_version_id: UUID | None
    current_content_html: str | None = None
    current_content_plain: str | None = None
    created_at: datetime
    updated_at: datetime


class SOPGrammarIssue(BaseModel):
    issue: str
    suggestion: str
    reason: str


class SOPGrammarResponse(BaseModel):
    corrected_text: str
    issues: list[SOPGrammarIssue]
    issue_count: int


class SOPScoreBreakdown(BaseModel):
    overall: float
    clarity: float
    structure: float
    uniqueness: float
    program_fit: float
    feedback: list[str]
    reasons: dict[str, str]


class SOPPlagiarismResponse(BaseModel):
    check_id: str
    status: str
    similarity_percent: float | None
    message: str
    report_available: bool
    reason: str


class SOPVersionCompareResponse(BaseModel):
    version_a: SOPVersionResponse
    version_b: SOPVersionResponse
    word_count_delta: int
    similarity_percent: float
    diff_summary: str


class SOPExportResponse(BaseModel):
    format: str
    filename: str
    content_base64: str | None = None
    content_text: str | None = None
    mime_type: str


class SOPAIActionResponse(BaseModel):
    content_html: str
    content_plain: str
    word_count: int
    version_id: UUID
    reason: str
    change_summary: str


class SOPCollaborationSessionResponse(BaseModel):
    id: UUID
    session_token: str
    role: str
    user_id: UUID
    is_active: bool
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class SOPStudioAnalyticsResponse(BaseModel):
    total_documents: int
    total_versions: int
    total_exports: int
    actions_by_type: dict[str, int]
    average_word_count: float
    documents_by_status: dict[str, int]
