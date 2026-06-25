from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_session import ChatSession
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ChatSession)

    async def get_by_user(self, user_id: UUID, *, active_only: bool = True) -> list[ChatSession]:
        stmt = select(ChatSession).where(ChatSession.user_id == user_id)
        if active_only:
            stmt = stmt.where(ChatSession.is_active.is_(True))
        stmt = stmt.order_by(ChatSession.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(self, session_id: UUID, user_id: UUID) -> ChatSession | None:
        result = await self.db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
