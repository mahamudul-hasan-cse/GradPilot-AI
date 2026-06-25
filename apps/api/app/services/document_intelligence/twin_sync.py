"""Synchronize extracted document data to Student Digital Twin."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_intelligence import DocumentUpload
from app.repositories.student_profile import StudentProfileRepository
from app.services.digital_twin.orchestrator import AIOrchestrator
from app.services.digital_twin.types import TwinEventType


class TwinSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.orchestrator = AIOrchestrator(db)
        self.profile_repo = StudentProfileRepository(db)

    async def on_document_processed(self, doc: DocumentUpload) -> None:
        await self._update_profile_from_extraction(doc)
        await self.orchestrator.publish_event(
            user_id=doc.user_id,
            event_type=TwinEventType.DOCUMENT_UPLOADED,
            source_service="document_intelligence",
            payload={
                "title": f"Document processed: {doc.file_name}",
                "description": f"Extracted {doc.classified_type} with confidence {doc.confidence_score}",
                "document_id": str(doc.id),
                "document_type": doc.classified_type,
                "extracted_fields": doc.extracted_fields,
                "confidence_score": float(doc.confidence_score or 0),
            },
            auto_refresh=True,
        )

    async def on_document_uploaded(self, doc: DocumentUpload) -> None:
        await self.orchestrator.publish_event(
            user_id=doc.user_id,
            event_type=TwinEventType.DOCUMENT_UPLOADED,
            source_service="document_intelligence",
            payload={
                "title": f"Document uploaded: {doc.file_name}",
                "document_id": str(doc.id),
                "document_type": doc.document_type,
            },
            auto_refresh=False,
        )

    async def _update_profile_from_extraction(self, doc: DocumentUpload) -> None:
        fields = doc.extracted_fields or {}
        profile = await self.profile_repo.get_by_user_id(doc.user_id)
        if not profile:
            return

        if doc.classified_type == "ielts_trf" and fields.get("overall_band"):
            scores = dict(profile.test_scores or {})
            scores["ielts"] = float(fields["overall_band"])
            profile.test_scores = scores
        elif doc.classified_type == "toefl" and fields.get("total_score"):
            scores = dict(profile.test_scores or {})
            scores["toefl"] = int(fields["total_score"])
            profile.test_scores = scores
        elif doc.classified_type == "gre" and fields.get("total"):
            scores = dict(profile.test_scores or {})
            scores["gre"] = int(fields["total"])
            profile.test_scores = scores
        elif doc.classified_type == "transcript" and fields.get("cgpa"):
            try:
                profile.gpa = float(str(fields["cgpa"]).split("/")[0])
            except ValueError:
                pass
        elif doc.classified_type == "passport" and fields.get("nationality"):
            profile.nationality = fields["nationality"]

        await self.db.flush()
