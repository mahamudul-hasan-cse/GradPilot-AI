"""Document Intelligence Platform — upload, parse, validate, sync."""

from __future__ import annotations

import logging
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document_intelligence import SUPPORTED_DOCUMENT_TYPES, DocumentProcessingJob, DocumentUpload
from app.models.user import User
from app.repositories.document_intelligence import DocumentJobRepository, DocumentUploadRepository
from app.schemas.document_intelligence import (
    DocumentJobResponse,
    DocumentUploadResponse,
    DocumentVersionResponse,
    ParseDocumentResponse,
    ValidationResponse,
)
from app.services.document_intelligence.pipeline import DocumentPipeline
from app.services.document_intelligence.queue import DocumentProcessingQueue
from app.services.document_intelligence.twin_sync import TwinSyncService

logger = logging.getLogger(__name__)

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str | None, default: str = "document") -> str:
    """Reduce a client-supplied filename to a safe basename (no separators, no '..')."""
    if not filename:
        return default
    # Take the last component under both POSIX and Windows separator rules.
    name = PureWindowsPath(PurePosixPath(filename.replace("\x00", "")).name).name
    name = _UNSAFE_FILENAME_CHARS.sub("_", name).strip("._")
    return name[:200] or default


class DocumentIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentUploadRepository(db)
        self.job_repo = DocumentJobRepository(db)
        self.pipeline = DocumentPipeline(db)
        self.queue = DocumentProcessingQueue()
        self.twin_sync = TwinSyncService(db)
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        Path(settings.document_upload_dir).mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        user: User,
        file: UploadFile,
        *,
        document_type: str | None = None,
        application_id: UUID | None = None,
        parent_id: UUID | None = None,
        background_tasks: BackgroundTasks | None = None,
    ) -> DocumentUploadResponse:
        if document_type and document_type not in SUPPORTED_DOCUMENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported document type: {document_type}")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")

        file_hash = DocumentUploadRepository.compute_hash(content)
        version = 1
        if parent_id:
            parent = await self.doc_repo.get_for_user(parent_id, user.id)
            if not parent:
                raise HTTPException(status_code=404, detail="Parent document not found")
            version = parent.version + 1

        doc_id = uuid4()
        original_name = sanitize_filename(file.filename)
        safe_name = f"{doc_id}_{original_name}"
        # NOTE: this is local container disk. On App Service with
        # WEBSITES_ENABLE_APP_SERVICE_STORAGE=false it is ephemeral, so files are
        # lost on restart/redeploy/scale-out while DB rows keep pointing at them.
        # Move to Azure Blob storage before relying on uploads in production.
        file_path = Path(settings.document_upload_dir) / safe_name
        file_path.write_bytes(content)
        file_url = f"/uploads/{safe_name}"

        doc = DocumentUpload(
            id=doc_id,
            user_id=user.id,
            application_id=application_id,
            parent_id=parent_id,
            version=version,
            document_type=document_type,
            file_name=original_name,
            file_url=file_url,
            file_hash=file_hash,
            mime_type=file.content_type,
            file_size_bytes=len(content),
            status="uploaded",
        )
        created = await self.doc_repo.create(doc)
        await self.twin_sync.on_document_uploaded(created)

        job = DocumentProcessingJob(
            document_id=created.id,
            user_id=user.id,
            status="pending",
        )
        job = await self.job_repo.create(job)
        queue_pos = await self.queue.enqueue(job.id, created.id, user.id)
        job.queue_position = queue_pos
        created.status = "queued"
        await self.doc_repo.update(created)

        if background_tasks:
            background_tasks.add_task(self._process_async, created.id, job.id)
        else:
            await self.pipeline.process(created.id, job.id)

        return self._to_response(created)

    async def _process_async(self, document_id: UUID, job_id: UUID) -> None:
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            try:
                pipeline = DocumentPipeline(session)
                await pipeline.process(document_id, job_id)
                await session.commit()
            except Exception as exc:
                logger.error("Async document processing failed: %s", exc)
                await session.rollback()

    async def list_documents(self, user: User, *, skip: int = 0, limit: int = 50) -> list[DocumentUploadResponse]:
        docs = await self.doc_repo.get_by_user(user.id, skip=skip, limit=limit)
        return [self._to_response(d) for d in docs]

    async def get_document(self, user: User, document_id: UUID) -> DocumentUploadResponse:
        doc = await self.doc_repo.get_for_user(document_id, user.id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return self._to_response(doc)

    async def parse_document(self, user: User, document_id: UUID) -> ParseDocumentResponse:
        doc = await self.doc_repo.get_for_user(document_id, user.id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        job = DocumentProcessingJob(document_id=doc.id, user_id=user.id, status="pending")
        job = await self.job_repo.create(job)
        result = await self.pipeline.process(doc.id, job.id)
        return ParseDocumentResponse(
            document_id=document_id,
            job_id=job.id,
            status=result.status,
            classified_type=result.classified_type,
            extracted_fields=result.extracted_fields,
            confidence_score=result.confidence_score,
            is_duplicate=result.is_duplicate,
        )

    async def validate_document(self, user: User, document_id: UUID) -> ValidationResponse:
        doc = await self.doc_repo.get_for_user(document_id, user.id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        if not doc.extracted_fields:
            raise HTTPException(status_code=400, detail="Document not yet parsed")
        from app.services.document_intelligence.validator import ValidationEngine

        validation = ValidationEngine().validate(doc.classified_type or "unknown", doc.extracted_fields)
        doc.validation_result = {
            "is_valid": validation.is_valid,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "passed_rules": validation.passed_rules,
        }
        await self.doc_repo.update(doc)
        return ValidationResponse(
            document_id=document_id,
            is_valid=validation.is_valid,
            errors=validation.errors,
            warnings=validation.warnings,
            passed_rules=validation.passed_rules,
        )

    async def get_versions(self, user: User, document_id: UUID) -> DocumentVersionResponse:
        doc = await self.doc_repo.get_for_user(document_id, user.id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        root_id = doc.parent_id or doc.id
        versions = await self.doc_repo.get_versions(root_id, user.id)
        return DocumentVersionResponse(
            root_id=root_id,
            versions=[self._to_response(v) for v in versions],
            total=len(versions),
        )

    async def get_job(self, user: User, job_id: UUID) -> DocumentJobResponse:
        job = await self.job_repo.get_for_user(job_id, user.id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return DocumentJobResponse(
            id=job.id,
            document_id=job.document_id,
            status=job.status,
            stage=job.stage,
            error_message=job.error_message,
            queue_position=job.queue_position,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
        )

    def _to_response(self, doc: DocumentUpload) -> DocumentUploadResponse:
        return DocumentUploadResponse(
            id=doc.id,
            user_id=doc.user_id,
            application_id=doc.application_id,
            parent_id=doc.parent_id,
            version=doc.version,
            document_type=doc.document_type,
            classified_type=doc.classified_type,
            file_name=doc.file_name,
            file_url=doc.file_url,
            file_hash=doc.file_hash,
            mime_type=doc.mime_type,
            file_size_bytes=doc.file_size_bytes,
            status=doc.status,
            extracted_fields=doc.extracted_fields,
            validation_result=doc.validation_result,
            confidence_score=float(doc.confidence_score) if doc.confidence_score else None,
            is_duplicate=doc.is_duplicate,
            duplicate_of_id=doc.duplicate_of_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
