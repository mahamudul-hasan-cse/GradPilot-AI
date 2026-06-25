from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    application_id: UUID | None
    parent_id: UUID | None
    version: int
    document_type: str | None
    classified_type: str | None
    file_name: str
    file_url: str | None
    file_hash: str | None
    mime_type: str | None
    file_size_bytes: int | None
    status: str
    extracted_fields: dict[str, Any] | None
    validation_result: dict[str, Any] | None
    confidence_score: float | None
    is_duplicate: bool
    duplicate_of_id: UUID | None
    created_at: datetime
    updated_at: datetime


class DocumentJobResponse(BaseModel):
    id: UUID
    document_id: UUID
    status: str
    stage: str | None
    error_message: str | None
    queue_position: int | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class ParseDocumentResponse(BaseModel):
    document_id: UUID
    job_id: UUID
    status: str
    classified_type: str
    extracted_fields: dict[str, Any]
    confidence_score: float
    is_duplicate: bool


class ValidationResponse(BaseModel):
    document_id: UUID
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    passed_rules: list[str]


class DocumentVersionResponse(BaseModel):
    root_id: UUID
    versions: list[DocumentUploadResponse]
    total: int
