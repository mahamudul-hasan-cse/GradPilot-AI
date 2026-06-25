"""Application Workspace — extended tables

Revision ID: 008_application_workspace
Revises: 007_knowledge_platform
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "008_application_workspace"
down_revision: Union[str, None] = "007_knowledge_platform"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APPLICATION_STATUSES = (
    "planning",
    "preparing",
    "ready",
    "submitted",
    "interview",
    "accepted",
    "rejected",
    "deferred",
    "withdrawn",
)


def upgrade() -> None:
    op.add_column("applications", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("applications", sa.Column("intake_term", sa.String(length=50), nullable=True))
    op.add_column(
        "applications",
        sa.Column("progress_percent", sa.Numeric(precision=5, scale=2), server_default="0", nullable=False),
    )
    op.add_column("applications", sa.Column("progress_breakdown", JSON(), nullable=True))
    op.add_column(
        "applications",
        sa.Column("profile_complete", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "applications",
        sa.Column("documents_complete", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "applications",
        sa.Column("sop_complete", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "applications",
        sa.Column("lor_complete", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "applications",
        sa.Column("submitted_complete", sa.Boolean(), server_default="false", nullable=False),
    )

    op.execute(
        """
        UPDATE applications SET status = CASE
            WHEN status = 'draft' THEN 'planning'
            WHEN status = 'in_progress' THEN 'preparing'
            ELSE status
        END
        """
    )

    op.create_table(
        "application_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=500), nullable=True),
        sa.Column("file_url", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_application_documents_application_id"),
        "application_documents",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_documents_document_type"),
        "application_documents",
        ["document_type"],
        unique=False,
    )

    op.create_table(
        "application_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_auto_generated", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_application_tasks_application_id"), "application_tasks", ["application_id"], unique=False)
    op.create_index(op.f("ix_application_tasks_status"), "application_tasks", ["status"], unique=False)

    op.create_table(
        "application_notes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_application_notes_application_id"), "application_notes", ["application_id"], unique=False)

    op.create_table(
        "application_activity",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_application_activity_application_id"),
        "application_activity",
        ["application_id"],
        unique=False,
    )
    op.create_index(op.f("ix_application_activity_event_type"), "application_activity", ["event_type"], unique=False)

    op.create_table(
        "application_deadlines",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("deadline_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("reminder_days_before", sa.Integer(), server_default="7", nullable=False),
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_completed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_application_deadlines_application_id"),
        "application_deadlines",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_deadlines_deadline_type"),
        "application_deadlines",
        ["deadline_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_deadlines_due_date"),
        "application_deadlines",
        ["due_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_application_deadlines_due_date"), table_name="application_deadlines")
    op.drop_index(op.f("ix_application_deadlines_deadline_type"), table_name="application_deadlines")
    op.drop_index(op.f("ix_application_deadlines_application_id"), table_name="application_deadlines")
    op.drop_table("application_deadlines")
    op.drop_index(op.f("ix_application_activity_event_type"), table_name="application_activity")
    op.drop_index(op.f("ix_application_activity_application_id"), table_name="application_activity")
    op.drop_table("application_activity")
    op.drop_index(op.f("ix_application_notes_application_id"), table_name="application_notes")
    op.drop_table("application_notes")
    op.drop_index(op.f("ix_application_tasks_status"), table_name="application_tasks")
    op.drop_index(op.f("ix_application_tasks_application_id"), table_name="application_tasks")
    op.drop_table("application_tasks")
    op.drop_index(op.f("ix_application_documents_document_type"), table_name="application_documents")
    op.drop_index(op.f("ix_application_documents_application_id"), table_name="application_documents")
    op.drop_table("application_documents")
    op.drop_column("applications", "submitted_complete")
    op.drop_column("applications", "lor_complete")
    op.drop_column("applications", "sop_complete")
    op.drop_column("applications", "documents_complete")
    op.drop_column("applications", "profile_complete")
    op.drop_column("applications", "progress_breakdown")
    op.drop_column("applications", "progress_percent")
    op.drop_column("applications", "intake_term")
    op.drop_column("applications", "title")
