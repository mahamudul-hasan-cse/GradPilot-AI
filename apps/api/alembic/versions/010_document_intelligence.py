"""Document Intelligence Platform tables

Revision ID: 010_document_intelligence
Revises: 009_digital_twin
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "010_document_intelligence"
down_revision: Union[str, None] = "009_digital_twin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_uploads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=True),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=True),
        sa.Column("classified_type", sa.String(length=50), nullable=True),
        sa.Column("file_name", sa.String(length=500), nullable=False),
        sa.Column("file_url", sa.String(length=1000), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="uploaded", nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("extracted_fields", JSON(), nullable=True),
        sa.Column("validation_result", JSON(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("duplicate_of_id", sa.UUID(), nullable=True),
        sa.Column("processing_metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["duplicate_of_id"], ["document_uploads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_id"], ["document_uploads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_uploads_user_id"), "document_uploads", ["user_id"], unique=False)
    op.create_index(op.f("ix_document_uploads_file_hash"), "document_uploads", ["file_hash"], unique=False)
    op.create_index(op.f("ix_document_uploads_status"), "document_uploads", ["status"], unique=False)
    op.create_index(op.f("ix_document_uploads_document_type"), "document_uploads", ["document_type"], unique=False)

    op.create_table(
        "document_processing_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("stage", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("queue_position", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document_uploads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_processing_jobs_document_id"), "document_processing_jobs", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_processing_jobs_status"), "document_processing_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_processing_jobs_status"), table_name="document_processing_jobs")
    op.drop_index(op.f("ix_document_processing_jobs_document_id"), table_name="document_processing_jobs")
    op.drop_table("document_processing_jobs")
    op.drop_index(op.f("ix_document_uploads_document_type"), table_name="document_uploads")
    op.drop_index(op.f("ix_document_uploads_status"), table_name="document_uploads")
    op.drop_index(op.f("ix_document_uploads_file_hash"), table_name="document_uploads")
    op.drop_index(op.f("ix_document_uploads_user_id"), table_name="document_uploads")
    op.drop_table("document_uploads")
