"""Student Digital Twin & event log

Revision ID: 009_digital_twin
Revises: 008_application_workspace
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "009_digital_twin"
down_revision: Union[str, None] = "008_application_workspace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "student_digital_twins",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("state_snapshot", JSON(), nullable=False),
        sa.Column("academic_profile", JSON(), nullable=True),
        sa.Column("language_tests", JSON(), nullable=True),
        sa.Column("documents", JSON(), nullable=True),
        sa.Column("applications", JSON(), nullable=True),
        sa.Column("universities", JSON(), nullable=True),
        sa.Column("scholarships", JSON(), nullable=True),
        sa.Column("recommendations", JSON(), nullable=True),
        sa.Column("deadlines", JSON(), nullable=True),
        sa.Column("preferences", JSON(), nullable=True),
        sa.Column("goals", JSON(), nullable=True),
        sa.Column("achievements", JSON(), nullable=True),
        sa.Column("weaknesses", JSON(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_student_digital_twins_user_id"), "student_digital_twins", ["user_id"], unique=True)

    op.create_table(
        "twin_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("source_service", sa.String(length=80), nullable=False),
        sa.Column("payload", JSON(), nullable=False),
        sa.Column("processed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_twin_events_user_id"), "twin_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_twin_events_event_type"), "twin_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_twin_events_processed"), "twin_events", ["processed"], unique=False)

    op.create_table(
        "twin_timeline",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("entry_metadata", JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["twin_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_twin_timeline_user_id"), "twin_timeline", ["user_id"], unique=False)
    op.create_index(op.f("ix_twin_timeline_occurred_at"), "twin_timeline", ["occurred_at"], unique=False)
