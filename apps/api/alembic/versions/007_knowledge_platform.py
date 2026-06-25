"""Knowledge base documents for RAG retrieval

Revision ID: 007_knowledge_platform
Revises: 006_profile_analysis
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "007_knowledge_platform"
down_revision: Union[str, None] = "006_profile_analysis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("token_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_documents_source_type"), "knowledge_documents", ["source_type"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_source_id"), "knowledge_documents", ["source_id"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_title"), "knowledge_documents", ["title"], unique=False)

    op.execute(
        """
        CREATE INDEX ix_knowledge_documents_content_fts
        ON knowledge_documents
        USING gin (to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, '')))
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_documents_content_fts")
    op.drop_index(op.f("ix_knowledge_documents_title"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_source_id"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_source_type"), table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
