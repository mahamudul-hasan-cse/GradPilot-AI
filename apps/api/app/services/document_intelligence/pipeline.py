"""Document processing pipeline orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_intelligence import DocumentProcessingJob, DocumentUpload
from app.repositories.document_intelligence import DocumentJobRepository, DocumentUploadRepository
from app.services.document_intelligence.classifier import DocumentClassifier
from app.services.document_intelligence.confidence import ConfidenceScorer
from app.services.document_intelligence.deduplicator import DuplicateDetector
from app.services.document_intelligence.extractors import get_extractor
from app.services.document_intelligence.ocr.providers import get_ocr_provider
from app.services.document_intelligence.twin_sync import TwinSyncService
from app.services.document_intelligence.types import PipelineResult
from app.services.document_intelligence.validator import ValidationEngine


class DocumentPipeline:
    STAGES = ("ocr", "classify", "extract", "validate", "score", "sync")

    def __init__(self, db: AsyncSession, *, ocr_provider: str = "fallback"):
        self.db = db
        self.doc_repo = DocumentUploadRepository(db)
        self.job_repo = DocumentJobRepository(db)
        self.ocr = get_ocr_provider(ocr_provider)
        self.classifier = DocumentClassifier()
        self.validator = ValidationEngine()
        self.scorer = ConfidenceScorer()
        self.deduplicator = DuplicateDetector(db)
        self.twin_sync = TwinSyncService(db)

    async def process(self, document_id: UUID, job_id: UUID | None = None) -> PipelineResult:
        doc = await self.doc_repo.get_by_id(document_id)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")

        job = await self._get_or_create_job(doc, job_id)
        job.status = "processing"
        job.started_at = datetime.now(UTC)
        doc.status = "processing"
        await self.db.flush()

        try:
            content = await self._load_content(doc)
            job.stage = "ocr"
            ocr_result = await self.ocr.extract_text(
                content=content, file_name=doc.file_name, mime_type=doc.mime_type
            )
            doc.raw_text = ocr_result.raw_text

            job.stage = "classify"
            classification = self.classifier.classify(
                ocr_result.raw_text,
                file_name=doc.file_name,
                hint_type=doc.document_type,
            )
            doc.classified_type = classification.document_type

            job.stage = "extract"
            extractor = get_extractor(classification.document_type)
            if extractor:
                extraction = extractor.extract(ocr_result.raw_text)
            else:
                from app.services.document_intelligence.types import ExtractionResult
                extraction = ExtractionResult(classification.document_type, {}, 0.2)

            doc.extracted_fields = extraction.fields

            job.stage = "validate"
            validation = self.validator.validate(classification.document_type, extraction.fields)
            doc.validation_result = {
                "is_valid": validation.is_valid,
                "errors": validation.errors,
                "warnings": validation.warnings,
                "passed_rules": validation.passed_rules,
            }

            job.stage = "score"
            confidence = self.scorer.score(
                classification=classification,
                extraction=extraction,
                validation=validation,
                ocr_confidence=ocr_result.confidence,
            )
            doc.confidence_score = confidence

            duplicate = await self.deduplicator.find_duplicate(doc.user_id, doc.file_hash or "")
            if duplicate and duplicate.id != doc.id:
                doc.is_duplicate = True
                doc.duplicate_of_id = duplicate.id
                doc.status = "duplicate"
            else:
                doc.status = "validated" if validation.is_valid else "parsed"

            doc.processing_metadata = {
                "ocr_provider": ocr_result.provider,
                "classification_signals": classification.signals,
                "field_confidence": extraction.field_confidence,
            }

            job.stage = "sync"
            if not doc.is_duplicate and validation.is_valid:
                await self.twin_sync.on_document_processed(doc)

            job.status = "completed"
            job.completed_at = datetime.now(UTC)
            await self.doc_repo.update(doc)
            await self.job_repo.update(job)

            return PipelineResult(
                document_id=str(doc.id),
                status=doc.status,
                classified_type=doc.classified_type or "unknown",
                extracted_fields=doc.extracted_fields or {},
                validation=validation,
                confidence_score=float(confidence),
                is_duplicate=doc.is_duplicate,
                version=doc.version,
            )
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(UTC)
            doc.status = "failed"
            await self.job_repo.update(job)
            await self.doc_repo.update(doc)
            raise

    async def _get_or_create_job(self, doc: DocumentUpload, job_id: UUID | None) -> DocumentProcessingJob:
        if job_id:
            job = await self.job_repo.get_by_id(job_id)
            if job:
                return job
        job = DocumentProcessingJob(document_id=doc.id, user_id=doc.user_id, status="pending")
        return await self.job_repo.create(job)

    async def _load_content(self, doc: DocumentUpload) -> bytes:
        from app.services.document_intelligence.storage import get_upload_storage

        content = get_upload_storage().load(doc.file_url)
        if content is not None:
            return content
        return doc.file_name.encode("utf-8")
