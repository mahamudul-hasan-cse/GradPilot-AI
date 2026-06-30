"""Plagiarism check placeholder interface."""

from __future__ import annotations

import uuid


class SOPPlagiarismService:
    """Placeholder for external plagiarism API integration (Turnitin, Copyleaks, etc.)."""

    async def check(self, *, content: str, document_id: str) -> dict:
        word_count = len(content.split())
        return {
            "check_id": str(uuid.uuid4()),
            "status": "placeholder",
            "similarity_percent": None,
            "message": (
                "Plagiarism scanning is not yet connected to an external provider. "
                "This placeholder records your check request for future integration."
            ),
            "report_available": False,
            "reason": (
                f"Placeholder check queued for document {document_id} ({word_count} words). "
                "Connect TURNITIN_API_KEY or COPYLEAKS_API_KEY to enable real similarity detection."
            ),
        }
