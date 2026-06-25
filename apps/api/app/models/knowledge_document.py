"""Knowledge documents for the AI Knowledge Platform."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    source_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    doc_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
