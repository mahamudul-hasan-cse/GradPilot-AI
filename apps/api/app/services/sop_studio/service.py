"""SOP Studio service — document lifecycle, AI actions, collaboration."""

from __future__ import annotations

import json
import logging
import secrets
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sop_studio import (
    SOPCollaborationSession,
    SOPComment,
    SOPDocument,
    SOPHistory,
    SOPVersion,
)
from app.models.user import User
from app.repositories.sop_studio import (
    SOPCollaborationRepository,
    SOPCommentRepository,
    SOPDocumentRepository,
    SOPHistoryRepository,
    SOPVersionRepository,
)
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
from app.services.digital_twin.aggregator import TwinAggregator
from app.services.digital_twin.orchestrator import AIOrchestrator
from app.services.digital_twin.types import TwinEventType
from app.services.sop_studio.draft_engine import SOPDraftEngine
from app.services.sop_studio.export_engine import SOPExportEngine
from app.services.sop_studio.grammar_engine import SOPGrammarEngine
from app.services.sop_studio.plagiarism import SOPPlagiarismService
from app.services.sop_studio.rewrite_engine import SOPRewriteEngine
from app.services.sop_studio.scoring_engine import SOPScoringEngine
from app.services.sop_studio.tailoring_engine import SOPTailoringEngine
from app.services.sop_studio.utils import (
    count_words,
    diff_summary,
    html_to_plain,
    plain_to_html,
    text_similarity,
)

logger = logging.getLogger(__name__)


class SOPStudioService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = SOPDocumentRepository(db)
        self.version_repo = SOPVersionRepository(db)
        self.comment_repo = SOPCommentRepository(db)
        self.history_repo = SOPHistoryRepository(db)
        self.collab_repo = SOPCollaborationRepository(db)
        self.aggregator = TwinAggregator(db)
        self.draft_engine = SOPDraftEngine()
        self.rewrite_engine = SOPRewriteEngine()
        self.grammar_engine = SOPGrammarEngine()
        self.tailoring_engine = SOPTailoringEngine()
        self.scoring_engine = SOPScoringEngine()
        self.export_engine = SOPExportEngine()
        self.plagiarism_service = SOPPlagiarismService()

    async def list_documents(self, user_id: UUID, *, skip: int = 0, limit: int = 50) -> list[SOPDocumentResponse]:
        docs = await self.doc_repo.list_for_user(user_id, skip=skip, limit=limit)
        return [await self._to_document_response(d, include_content=False) for d in docs]

    async def create_document(self, user: User, data: SOPDocumentCreate) -> SOPDocumentResponse:
        doc = SOPDocument(
            user_id=user.id,
            title=data.title,
            target_type=data.target_type,
            application_id=data.application_id,
            university_id=data.university_id,
            scholarship_id=data.scholarship_id,
            university_name=data.university_name,
            program_name=data.program_name,
            scholarship_name=data.scholarship_name,
            target_word_count=data.target_word_count,
            status="draft",
        )
        doc = await self.doc_repo.create(doc)

        if data.initial_content:
            plain = data.initial_content
            html = plain_to_html(plain)
            version = await self._create_version(
                doc,
                user.id,
                content_html=html,
                content_plain=plain,
                source_action="create",
                change_summary="Initial content",
            )
            doc.current_version_id = version.id
            doc.word_count = version.word_count
            await self.doc_repo.update(doc)

        await self._log_history(doc.id, user.id, "created", details={"title": doc.title})
        await self._publish_twin_event(user.id, TwinEventType.SOP_CREATED, doc)
        return await self._to_document_response(doc)

    async def get_document(self, user_id: UUID, document_id: UUID) -> SOPDocumentResponse:
        doc = await self._require_document(document_id, user_id)
        return await self._to_document_response(doc, include_content=True)

    async def update_document(
        self, user_id: UUID, document_id: UUID, data: SOPDocumentUpdate
    ) -> SOPDocumentResponse:
        doc = await self._require_document(document_id, user_id)
        updates = data.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(doc, key, value)
        doc = await self.doc_repo.update(doc)
        await self._log_history(doc.id, user_id, "updated", details=updates)
        return await self._to_document_response(doc)

    async def delete_document(self, user_id: UUID, document_id: UUID) -> None:
        doc = await self._require_document(document_id, user_id)
        await self.doc_repo.delete(doc)

    async def autosave(
        self, user_id: UUID, document_id: UUID, data: SOPAutosaveRequest
    ) -> SOPDocumentResponse:
        doc = await self._require_document(document_id, user_id)
        plain = data.content_plain or html_to_plain(data.content_html)
        words = count_words(plain)

        version = await self._create_version(
            doc,
            user_id,
            content_html=data.content_html,
            content_plain=plain,
            source_action="autosave",
            change_summary="Autosave",
            is_autosave=True,
            version_metadata={"cursor_position": data.cursor_position},
        )

        doc.word_count = words
        if not doc.current_version_id:
            doc.current_version_id = version.id
        await self.doc_repo.update(doc)
        await self._log_history(
            doc.id, user_id, "autosave", version_id=version.id, details={"word_count": words}
        )
        return await self._to_document_response(doc, include_content=True)

    async def ai_draft(
        self, user: User, document_id: UUID, request: SOPDraftRequest
    ) -> SOPAIActionResponse:
        doc = await self._require_document(document_id, user.id)
        context = await self._build_student_context(user.id)
        target_words = request.target_word_count or doc.target_word_count

        plain, reason = await self.draft_engine.generate(
            student_context=context,
            university_name=doc.university_name,
            program_name=doc.program_name,
            scholarship_name=doc.scholarship_name,
            themes=request.themes,
            tone=request.tone,
            target_word_count=target_words,
            extra_prompt=request.prompt,
        )
        return await self._apply_ai_content(
            doc, user.id, plain, source_action="ai_draft", reason=reason, change_summary="AI draft generated"
        )

    async def ai_rewrite(
        self, user_id: UUID, document_id: UUID, request: SOPRewriteRequest
    ) -> SOPAIActionResponse:
        doc = await self._require_document(document_id, user_id)
        plain, reason = await self.rewrite_engine.rewrite(
            content=request.content_plain,
            instruction=request.instruction,
            section=request.section,
        )
        return await self._apply_ai_content(
            doc,
            user_id,
            plain,
            source_action="ai_rewrite",
            reason=reason,
            change_summary=f"Rewrite: {request.instruction[:120]}",
        )

    async def grammar_review(self, user_id: UUID, document_id: UUID, request: SOPGrammarRequest) -> SOPGrammarResponse:
        await self._require_document(document_id, user_id)
        corrected, issues = await self.grammar_engine.review(request.content_plain)
        await self._log_history(
            document_id,
            user_id,
            "grammar_review",
            details={"issue_count": len(issues)},
        )
        return SOPGrammarResponse(
            corrected_text=corrected,
            issues=issues,
            issue_count=len(issues),
        )

    async def tailor_university(
        self, user_id: UUID, document_id: UUID, request: SOPTailorUniversityRequest
    ) -> SOPAIActionResponse:
        doc = await self._require_document(document_id, user_id)
        plain, reason = await self.tailoring_engine.tailor_university(
            content=request.content_plain,
            university_name=request.university_name,
            program_name=request.program_name,
            highlights=request.highlights,
        )
        doc.university_name = request.university_name
        doc.program_name = request.program_name
        await self.doc_repo.update(doc)
        return await self._apply_ai_content(
            doc,
            user_id,
            plain,
            source_action="tailor_university",
            reason=reason,
            change_summary=f"Tailored for {request.university_name}",
        )

    async def tailor_scholarship(
        self, user_id: UUID, document_id: UUID, request: SOPTailorScholarshipRequest
    ) -> SOPAIActionResponse:
        doc = await self._require_document(document_id, user_id)
        plain, reason = await self.tailoring_engine.tailor_scholarship(
            content=request.content_plain,
            scholarship_name=request.scholarship_name,
            provider=request.provider,
            eligibility_notes=request.eligibility_notes,
        )
        doc.scholarship_name = request.scholarship_name
        await self.doc_repo.update(doc)
        return await self._apply_ai_content(
            doc,
            user_id,
            plain,
            source_action="tailor_scholarship",
            reason=reason,
            change_summary=f"Tailored for scholarship {request.scholarship_name}",
        )

    async def score_document(
        self, user_id: UUID, document_id: UUID, request: SOPScoreRequest
    ) -> SOPScoreBreakdown:
        doc = await self._require_document(document_id, user_id)
        breakdown = self.scoring_engine.score(request.content_plain, target_word_count=doc.target_word_count)
        await self._log_history(
            document_id,
            user_id,
            "scored",
            details={"overall": breakdown.overall},
        )
        await self._publish_twin_event(
            user_id,
            TwinEventType.SOP_SCORED,
            doc,
            payload={"overall_score": breakdown.overall},
        )
        return breakdown

    async def plagiarism_check(
        self, user_id: UUID, document_id: UUID, request: SOPScoreRequest
    ) -> SOPPlagiarismResponse:
        doc = await self._require_document(document_id, user_id)
        result = await self.plagiarism_service.check(content=request.content_plain, document_id=str(document_id))
        await self._log_history(document_id, user_id, "plagiarism_check", details={"check_id": result["check_id"]})
        return SOPPlagiarismResponse(**result)

    async def export_document(
        self, user_id: UUID, document_id: UUID, *, export_format: str
    ) -> SOPExportResponse:
        doc = await self._require_document(document_id, user_id)
        plain = await self._current_plain(doc)
        fmt = export_format.lower()

        if fmt == "markdown":
            data, filename, mime = self.export_engine.export_markdown(title=doc.title, content_plain=plain)
            return SOPExportResponse(
                format=fmt,
                filename=filename,
                content_text=data.decode("utf-8"),
                mime_type=mime,
            )
        if fmt == "docx":
            data, filename, mime = self.export_engine.export_docx(title=doc.title, content_plain=plain)
        elif fmt == "pdf":
            data, filename, mime = self.export_engine.export_pdf(title=doc.title, content_plain=plain)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported format: {export_format}")

        await self._log_history(document_id, user_id, "exported", details={"format": fmt})
        await self._publish_twin_event(user_id, TwinEventType.SOP_EXPORTED, doc, payload={"format": fmt})
        return SOPExportResponse(
            format=fmt,
            filename=filename,
            content_base64=self.export_engine.to_base64(data),
            mime_type=mime,
        )

    async def list_versions(self, user_id: UUID, document_id: UUID, *, include_autosave: bool = False) -> list[SOPVersionResponse]:
        await self._require_document(document_id, user_id)
        versions = await self.version_repo.get_by_document(document_id, include_autosave=include_autosave)
        return [self._to_version_response(v) for v in versions]

    async def get_version(self, user_id: UUID, document_id: UUID, version_id: UUID) -> SOPVersionResponse:
        await self._require_document(document_id, user_id)
        version = await self.version_repo.get_version(document_id, version_id)
        if not version:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
        return self._to_version_response(version)

    async def compare_versions(
        self, user_id: UUID, document_id: UUID, version_a_id: UUID, version_b_id: UUID
    ) -> SOPVersionCompareResponse:
        await self._require_document(document_id, user_id)
        va = await self.version_repo.get_version(document_id, version_a_id)
        vb = await self.version_repo.get_version(document_id, version_b_id)
        if not va or not vb:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both versions not found")

        similarity = text_similarity(va.content_plain, vb.content_plain)
        return SOPVersionCompareResponse(
            version_a=self._to_version_response(va),
            version_b=self._to_version_response(vb),
            word_count_delta=vb.word_count - va.word_count,
            similarity_percent=similarity,
            diff_summary=diff_summary(va.content_plain, vb.content_plain),
        )

    async def add_comment(
        self, user: User, document_id: UUID, data: SOPCommentCreate
    ) -> SOPCommentResponse:
        await self._require_document(document_id, user.id)
        comment = SOPComment(
            document_id=document_id,
            version_id=data.version_id,
            user_id=user.id,
            author_name=user.full_name,
            body=data.body,
            anchor_text=data.anchor_text,
        )
        comment = await self.comment_repo.create(comment)
        await self._log_history(document_id, user.id, "comment_added", version_id=data.version_id)
        return self._to_comment_response(comment)

    async def list_comments(self, user_id: UUID, document_id: UUID) -> list[SOPCommentResponse]:
        await self._require_document(document_id, user_id)
        comments = await self.comment_repo.get_by_document(document_id)
        return [self._to_comment_response(c) for c in comments]

    async def resolve_comment(self, user_id: UUID, document_id: UUID, comment_id: UUID) -> SOPCommentResponse:
        await self._require_document(document_id, user_id)
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment or comment.document_id != document_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        comment.is_resolved = True
        comment = await self.comment_repo.update(comment)
        return self._to_comment_response(comment)

    async def list_history(self, user_id: UUID, document_id: UUID) -> list[SOPHistoryResponse]:
        await self._require_document(document_id, user_id)
        entries = await self.history_repo.get_by_document(document_id)
        return [SOPHistoryResponse.model_validate(e) for e in entries]

    async def join_collaboration(
        self, user: User, document_id: UUID, data: SOPCollaborationJoinRequest
    ) -> SOPCollaborationSessionResponse:
        await self._require_document(document_id, user.id)
        session = SOPCollaborationSession(
            document_id=document_id,
            user_id=user.id,
            session_token=secrets.token_urlsafe(32),
            role=data.role,
            is_active=True,
            last_seen_at=datetime.now(UTC),
        )
        session = await self.collab_repo.create(session)
        await self._log_history(document_id, user.id, "collaboration_join", details={"role": data.role})
        return SOPCollaborationSessionResponse.model_validate(session)

    async def list_collaboration_sessions(
        self, user_id: UUID, document_id: UUID
    ) -> list[SOPCollaborationSessionResponse]:
        await self._require_document(document_id, user_id)
        sessions = await self.collab_repo.get_active_sessions(document_id)
        return [SOPCollaborationSessionResponse.model_validate(s) for s in sessions]

    async def collaboration_heartbeat(
        self, user_id: UUID, document_id: UUID, session_token: str, *, cursor_position: int | None = None
    ) -> SOPCollaborationSessionResponse:
        await self._require_document(document_id, user_id)
        session = await self.collab_repo.get_by_token(session_token)
        if not session or session.document_id != document_id or session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collaboration session not found")
        session.last_seen_at = datetime.now(UTC)
        if cursor_position is not None:
            session.cursor_position = cursor_position
        session = await self.collab_repo.update(session)
        return SOPCollaborationSessionResponse.model_validate(session)

    async def word_count(self, user_id: UUID, document_id: UUID) -> dict:
        doc = await self._require_document(document_id, user_id)
        plain = await self._current_plain(doc)
        return {
            "word_count": count_words(plain),
            "target_word_count": doc.target_word_count,
            "delta": count_words(plain) - doc.target_word_count,
        }

    async def analytics(self, user_id: UUID) -> SOPStudioAnalyticsResponse:
        docs = await self.doc_repo.list_for_user(user_id, limit=500)
        doc_ids = [d.id for d in docs]
        total_versions = 0
        total_exports = 0
        actions: dict[str, int] = {}
        word_sum = 0

        if doc_ids:
            version_count = await self.db.execute(
                select(func.count())
                .select_from(SOPVersion)
                .where(SOPVersion.document_id.in_(doc_ids), SOPVersion.is_autosave.is_(False))
            )
            total_versions = version_count.scalar_one() or 0

            history_rows = await self.db.execute(
                select(SOPHistory.action, func.count())
                .where(SOPHistory.document_id.in_(doc_ids))
                .group_by(SOPHistory.action)
            )
            actions = {row[0]: row[1] for row in history_rows.all()}
            total_exports = actions.get("exported", 0)

        for d in docs:
            word_sum += d.word_count

        status_counts: dict[str, int] = {}
        for d in docs:
            status_counts[d.status] = status_counts.get(d.status, 0) + 1

        avg_words = round(word_sum / len(docs), 1) if docs else 0.0
        return SOPStudioAnalyticsResponse(
            total_documents=len(docs),
            total_versions=total_versions,
            total_exports=total_exports,
            actions_by_type=actions,
            average_word_count=avg_words,
            documents_by_status=status_counts,
        )

    async def _apply_ai_content(
        self,
        doc: SOPDocument,
        user_id: UUID,
        plain: str,
        *,
        source_action: str,
        reason: str,
        change_summary: str,
    ) -> SOPAIActionResponse:
        html = plain_to_html(plain)
        version = await self._create_version(
            doc,
            user_id,
            content_html=html,
            content_plain=plain,
            source_action=source_action,
            change_summary=change_summary,
        )
        doc.current_version_id = version.id
        doc.word_count = version.word_count
        doc.status = "in_progress"
        await self.doc_repo.update(doc)
        await self._log_history(doc.id, user_id, source_action, version_id=version.id)
        await self._publish_twin_event(user_id, TwinEventType.SOP_UPDATED, doc, payload={"action": source_action})

        return SOPAIActionResponse(
            content_html=html,
            content_plain=plain,
            word_count=version.word_count,
            version_id=version.id,
            reason=reason,
            change_summary=change_summary,
        )

    async def _create_version(
        self,
        doc: SOPDocument,
        user_id: UUID,
        *,
        content_html: str,
        content_plain: str,
        source_action: str,
        change_summary: str | None = None,
        is_autosave: bool = False,
        version_metadata: dict | None = None,
    ) -> SOPVersion:
        next_num = await self.version_repo.get_latest_number(doc.id) + 1
        version = SOPVersion(
            document_id=doc.id,
            version_number=next_num,
            content_html=content_html,
            content_plain=content_plain,
            word_count=count_words(content_plain),
            change_summary=change_summary,
            source_action=source_action,
            is_autosave=is_autosave,
            version_metadata=version_metadata,
        )
        return await self.version_repo.create(version)

    async def _require_document(self, document_id: UUID, user_id: UUID) -> SOPDocument:
        doc = await self.doc_repo.get_for_user(document_id, user_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP document not found")
        return doc

    async def _current_plain(self, doc: SOPDocument) -> str:
        if doc.current_version_id:
            version = await self.version_repo.get_by_id(doc.current_version_id)
            if version:
                return version.content_plain
        return ""

    async def _build_student_context(self, user_id: UUID) -> str:
        twin = await self.aggregator.build_state(user_id)
        snapshot = twin.to_snapshot()
        return json.dumps(
            {
                "academic_profile": snapshot.get("academic_profile"),
                "language_tests": snapshot.get("language_tests"),
                "achievements": snapshot.get("achievements"),
                "goals": snapshot.get("goals"),
                "weaknesses": snapshot.get("weaknesses"),
                "preferences": snapshot.get("preferences"),
            },
            default=str,
        )

    async def _log_history(
        self,
        document_id: UUID,
        user_id: UUID,
        action: str,
        *,
        version_id: UUID | None = None,
        details: dict | None = None,
    ) -> None:
        entry = SOPHistory(
            document_id=document_id,
            user_id=user_id,
            action=action,
            version_id=version_id,
            details=details,
        )
        await self.history_repo.create(entry)

    async def _publish_twin_event(
        self,
        user_id: UUID,
        event_type: TwinEventType,
        doc: SOPDocument,
        *,
        payload: dict | None = None,
    ) -> None:
        try:
            orchestrator = AIOrchestrator(self.db)
            await orchestrator.publish_event(
                user_id=user_id,
                event_type=event_type,
                source_service="sop_studio",
                payload={
                    "document_id": str(doc.id),
                    "title": doc.title,
                    "word_count": doc.word_count,
                    **(payload or {}),
                },
            )
        except Exception:
            logger.exception("Failed to publish twin event %s for SOP %s", event_type, doc.id)

    async def _to_document_response(self, doc: SOPDocument, *, include_content: bool = True) -> SOPDocumentResponse:
        content_html = None
        content_plain = None
        if include_content and doc.current_version_id:
            version = await self.version_repo.get_by_id(doc.current_version_id)
            if version:
                content_html = version.content_html
                content_plain = version.content_plain
        return SOPDocumentResponse(
            id=doc.id,
            title=doc.title,
            target_type=doc.target_type,
            status=doc.status,
            word_count=doc.word_count,
            target_word_count=doc.target_word_count,
            university_name=doc.university_name,
            program_name=doc.program_name,
            scholarship_name=doc.scholarship_name,
            application_id=doc.application_id,
            current_version_id=doc.current_version_id,
            current_content_html=content_html,
            current_content_plain=content_plain,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    def _to_version_response(self, version: SOPVersion) -> SOPVersionResponse:
        return SOPVersionResponse.model_validate(version)

    def _to_comment_response(self, comment: SOPComment) -> SOPCommentResponse:
        return SOPCommentResponse.model_validate(comment)
