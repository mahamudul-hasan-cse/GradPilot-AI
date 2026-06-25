"""Duplicate document detection by file hash."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_intelligence import DocumentUpload


class DuplicateDetector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_duplicate(self, user_id: UUID, file_hash: str) -> DocumentUpload | None:
        if not file_hash:
            return None
        result = await self.db.execute(
            select(DocumentUpload)
            .where(
                DocumentUpload.user_id == user_id,
                DocumentUpload.file_hash == file_hash,
                DocumentUpload.is_duplicate.is_(False),
            )
            .order_by(DocumentUpload.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
