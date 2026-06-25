from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChatSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_sessions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(255))
    session_type: Mapped[str] = mapped_column(String(50), default="guidance", nullable=False)
    messages: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    session_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
