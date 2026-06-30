from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sop_studio import (
    SOPCollaborationSession,
    SOPComment,
    SOPDocument,
    SOPHistory,
    SOPVersion,
)
from app.repositories.base import BaseRepository


class SOPDocumentRepository(BaseRepository[SOPDocument]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SOPDocument)

    async def get_for_user(self, document_id: UUID, user_id: UUID) -> SOPDocument | None:
        result = await self.db.execute(
            select(SOPDocument).where(SOPDocument.id == document_id, SOPDocument.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: UUID, *, skip: int = 0, limit: int = 50) -> list[SOPDocument]:
        result = await self.db.execute(
            select(SOPDocument)
            .where(SOPDocument.user_id == user_id)
            .order_by(SOPDocument.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_for_user(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(SOPDocument).where(SOPDocument.user_id == user_id)
        )
        return result.scalar_one() or 0


class SOPVersionRepository(BaseRepository[SOPVersion]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SOPVersion)

    async def get_by_document(self, document_id: UUID, *, include_autosave: bool = False) -> list[SOPVersion]:
        stmt = select(SOPVersion).where(SOPVersion.document_id == document_id)
        if not include_autosave:
            stmt = stmt.where(SOPVersion.is_autosave.is_(False))
        stmt = stmt.order_by(SOPVersion.version_number.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_number(self, document_id: UUID) -> int:
        result = await self.db.execute(
            select(func.max(SOPVersion.version_number)).where(SOPVersion.document_id == document_id)
        )
        return result.scalar_one() or 0

    async def get_version(self, document_id: UUID, version_id: UUID) -> SOPVersion | None:
        result = await self.db.execute(
            select(SOPVersion).where(SOPVersion.id == version_id, SOPVersion.document_id == document_id)
        )
        return result.scalar_one_or_none()


class SOPCommentRepository(BaseRepository[SOPComment]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SOPComment)

    async def get_by_document(self, document_id: UUID) -> list[SOPComment]:
        result = await self.db.execute(
            select(SOPComment)
            .where(SOPComment.document_id == document_id)
            .order_by(SOPComment.created_at.asc())
        )
        return list(result.scalars().all())


class SOPHistoryRepository(BaseRepository[SOPHistory]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SOPHistory)

    async def get_by_document(self, document_id: UUID, *, limit: int = 100) -> list[SOPHistory]:
        result = await self.db.execute(
            select(SOPHistory)
            .where(SOPHistory.document_id == document_id)
            .order_by(SOPHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_action(self) -> dict[str, int]:
        result = await self.db.execute(select(SOPHistory.action, func.count()).group_by(SOPHistory.action))
        return {row[0]: row[1] for row in result.all()}


class SOPCollaborationRepository(BaseRepository[SOPCollaborationSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SOPCollaborationSession)

    async def get_active_sessions(self, document_id: UUID) -> list[SOPCollaborationSession]:
        result = await self.db.execute(
            select(SOPCollaborationSession).where(
                SOPCollaborationSession.document_id == document_id,
                SOPCollaborationSession.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def get_by_token(self, token: str) -> SOPCollaborationSession | None:
        result = await self.db.execute(
            select(SOPCollaborationSession).where(SOPCollaborationSession.session_token == token)
        )
        return result.scalar_one_or_none()
