"""Progress calculation engine for application workspace."""

from __future__ import annotations

from app.models.application import Application
from app.services.application_workspace.constants import PROGRESS_WEIGHTS


class ProgressEngine:
    def calculate(self, application: Application) -> dict:
        breakdown = {
            "profile_complete": {
                "label": "Profile Complete",
                "weight": PROGRESS_WEIGHTS["profile_complete"],
                "completed": application.profile_complete,
                "percent": PROGRESS_WEIGHTS["profile_complete"] if application.profile_complete else 0,
            },
            "documents_complete": {
                "label": "Documents",
                "weight": PROGRESS_WEIGHTS["documents_complete"],
                "completed": application.documents_complete,
                "percent": PROGRESS_WEIGHTS["documents_complete"] if application.documents_complete else 0,
            },
            "sop_complete": {
                "label": "SOP",
                "weight": PROGRESS_WEIGHTS["sop_complete"],
                "completed": application.sop_complete,
                "percent": PROGRESS_WEIGHTS["sop_complete"] if application.sop_complete else 0,
            },
            "lor_complete": {
                "label": "Recommendation Letter",
                "weight": PROGRESS_WEIGHTS["lor_complete"],
                "completed": application.lor_complete,
                "percent": PROGRESS_WEIGHTS["lor_complete"] if application.lor_complete else 0,
            },
            "submitted_complete": {
                "label": "Application Submitted",
                "weight": PROGRESS_WEIGHTS["submitted_complete"],
                "completed": application.submitted_complete,
                "percent": PROGRESS_WEIGHTS["submitted_complete"] if application.submitted_complete else 0,
            },
        }
        total = sum(item["percent"] for item in breakdown.values())
        return {
            "progress_percent": round(float(total), 2),
            "breakdown": breakdown,
        }

    def sync_flags_from_documents(self, application: Application) -> None:
        if not application.documents:
            return
        uploaded_types = {
            d.document_type
            for d in application.documents
            if d.status in {"uploaded", "verified"} and d.file_url
        }
        application.sop_complete = "sop" in uploaded_types
        application.lor_complete = "lor" in uploaded_types
        doc_types = {"transcript", "cv", "ielts", "passport", "financial"}
        application.documents_complete = bool(uploaded_types & doc_types)

    def sync_submitted_flag(self, application: Application) -> None:
        application.submitted_complete = application.status in {
            "submitted",
            "interview",
            "accepted",
            "rejected",
            "deferred",
        } or application.submitted_at is not None

    def apply_to_application(self, application: Application) -> dict:
        self.sync_flags_from_documents(application)
        self.sync_submitted_flag(application)
        result = self.calculate(application)
        application.progress_percent = result["progress_percent"]
        application.progress_breakdown = result["breakdown"]
        return result
