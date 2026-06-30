"""SOP Studio tables

Revision ID: 012_sop_studio
Revises: 011_ai_planner
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "012_sop_studio"
down_revision: Union[str, None] = "011_ai_planner"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sop_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("university_id", sa.UUID(), nullable=True),
        sa.Column("scholarship_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("target_type", sa.String(length=30), server_default="university", nullable=False),
        sa.Column("status", sa.String(length=30), server_default="draft", nullable=False),
        sa.Column("current_version_id", sa.UUID(), nullable=True),
        sa.Column("word_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("target_word_count", sa.Integer(), server_default="750", nullable=False),
        sa.Column("university_name", sa.String(length=500), nullable=True),
        sa.Column("program_name", sa.String(length=500), nullable=True),
        sa.Column("scholarship_name", sa.String(length=500), nullable=True),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sop_documents_user_id"), "sop_documents", ["user_id"], unique=False)
    op.create_index(op.f("ix_sop_documents_status"), "sop_documents", ["status"], unique=False)

    op.create_table(
        "sop_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content_html", sa.Text(), nullable=False),
        sa.Column("content_plain", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("change_summary", sa.String(length=500), nullable=True),
        sa.Column("source_action", sa.String(length=50), server_default="manual", nullable=False),
        sa.Column("is_autosave", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["sop_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sop_versions_document_id"), "sop_versions", ["document_id"], unique=False)

    op.create_table(
        "sop_comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("version_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("anchor_text", sa.String(length=500), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["sop_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["version_id"], ["sop_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sop_comments_document_id"), "sop_comments", ["document_id"], unique=False)

    op.create_table(
        "sop_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("version_id", sa.UUID(), nullable=True),
        sa.Column("details", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["sop_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["version_id"], ["sop_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sop_history_document_id"), "sop_history", ["document_id"], unique=False)
    op.create_index(op.f("ix_sop_history_action"), "sop_history", ["action"], unique=False)

    op.create_table(
        "sop_collaboration_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("session_token", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=30), server_default="editor", nullable=False),
        sa.Column("cursor_position", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["sop_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sop_collaboration_sessions_document_id"), "sop_collaboration_sessions", ["document_id"], unique=False)
    op.create_index(op.f("ix_sop_collaboration_sessions_session_token"), "sop_collaboration_sessions", ["session_token"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_sop_collaboration_sessions_session_token"), table_name="sop_collaboration_sessions")
    op.drop_index(op.f("ix_sop_collaboration_sessions_document_id"), table_name="sop_collaboration_sessions")
    op.drop_table("sop_collaboration_sessions")
    op.drop_index(op.f("ix_sop_history_action"), table_name="sop_history")
    op.drop_index(op.f("ix_sop_history_document_id"), table_name="sop_history")
    op.drop_table("sop_history")
    op.drop_index(op.f("ix_sop_comments_document_id"), table_name="sop_comments")
    op.drop_table("sop_comments")
    op.drop_index(op.f("ix_sop_versions_document_id"), table_name="sop_versions")
    op.drop_table("sop_versions")
    op.drop_index(op.f("ix_sop_documents_status"), table_name="sop_documents")
    op.drop_index(op.f("ix_sop_documents_user_id"), table_name="sop_documents")
    op.drop_table("sop_documents")
