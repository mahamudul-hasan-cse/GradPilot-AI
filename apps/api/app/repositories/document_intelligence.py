import hashlib
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_intelligence import DocumentProcessingJob, DocumentUpload
from app.repositories.base import BaseRepository


class DocumentUploadRepository(BaseRepository[DocumentUpload]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, DocumentUpload)

    async def get_by_user(self, user_id: UUID, *, skip: int = 0, limit: int = 50) -> list[DocumentUpload]:
        result = await self.db.execute(
            select(DocumentUpload)
            .where(DocumentUpload.user_id == user_id)
            .order_by(DocumentUpload.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_for_user(self, document_id: UUID, user_id: UUID) -> DocumentUpload | None:
        result = await self.db.execute(
            select(DocumentUpload).where(
                DocumentUpload.id == document_id,
                DocumentUpload.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_versions(self, parent_id: UUID, user_id: UUID) -> list[DocumentUpload]:
        result = await self.db.execute(
            select(DocumentUpload)
            .where(
                DocumentUpload.user_id == user_id,
                (DocumentUpload.id == parent_id) | (DocumentUpload.parent_id == parent_id),
            )
            .order_by(DocumentUpload.version.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def compute_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()


class DocumentJobRepository(BaseRepository[DocumentProcessingJob]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, DocumentProcessingJob)

    async def get_for_document(self, document_id: UUID) -> list[DocumentProcessingJob]:
        result = await self.db.execute(
            select(DocumentProcessingJob)
            .where(DocumentProcessingJob.document_id == document_id)
            .order_by(DocumentProcessingJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_user(self, job_id: UUID, user_id: UUID) -> DocumentProcessingJob | None:
        result = await self.db.execute(
            select(DocumentProcessingJob).where(
                DocumentProcessingJob.id == job_id,
                DocumentProcessingJob.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
