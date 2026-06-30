"""SOP Studio models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SOPDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sop_documents"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    application_id: Mapped[UUID | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"))
    university_id: Mapped[UUID | None] = mapped_column(nullable=True)
    scholarship_id: Mapped[UUID | None] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    target_type: Mapped[str] = mapped_column(String(30), default="university")
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    current_version_id: Mapped[UUID | None] = mapped_column(nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    target_word_count: Mapped[int] = mapped_column(Integer, default=750)
    university_name: Mapped[str | None] = mapped_column(String(500))
    program_name: Mapped[str | None] = mapped_column(String(500))
    scholarship_name: Mapped[str | None] = mapped_column(String(500))
    doc_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class SOPVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sop_versions"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("sop_documents.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)
    content_plain: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    change_summary: Mapped[str | None] = mapped_column(String(500))
    source_action: Mapped[str] = mapped_column(String(50), default="manual")
    is_autosave: Mapped[bool] = mapped_column(Boolean, default=False)
    version_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class SOPComment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sop_comments"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("sop_documents.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[UUID | None] = mapped_column(ForeignKey("sop_versions.id", ondelete="SET NULL"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    anchor_text: Mapped[str | None] = mapped_column(String(500))
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    comment_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class SOPHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sop_history"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("sop_documents.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column(String(50), index=True)
    version_id: Mapped[UUID | None] = mapped_column(ForeignKey("sop_versions.id", ondelete="SET NULL"))
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class SOPCollaborationSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sop_collaboration_sessions"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("sop_documents.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    session_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(30), default="editor")
    cursor_position: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    session_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
