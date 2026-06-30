"""AI Planner tables

Revision ID: 011_ai_planner
Revises: 010_document_intelligence
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "011_ai_planner"
down_revision: Union[str, None] = "010_document_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "planner_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("cache_key", sa.String(length=64), nullable=True),
        sa.Column("twin_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("priority_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("readiness_timeline", JSON(), nullable=True),
        sa.Column("request_payload", JSON(), nullable=False),
        sa.Column("response_summary", JSON(), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planner_history_user_id"), "planner_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_planner_history_cache_key"), "planner_history", ["cache_key"], unique=False)

    op.create_table(
        "planner_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("task_type", sa.String(length=50), server_default="action", nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("priority_score", sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column("priority_rank", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("time_horizon", sa.String(length=20), nullable=True),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["planner_history.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planner_tasks_user_id"), "planner_tasks", ["user_id"], unique=False)
    op.create_index(op.f("ix_planner_tasks_plan_id"), "planner_tasks", ["plan_id"], unique=False)
    op.create_index(op.f("ix_planner_tasks_scheduled_date"), "planner_tasks", ["scheduled_date"], unique=False)
    op.create_index(op.f("ix_planner_tasks_status"), "planner_tasks", ["status"], unique=False)

    op.create_table(
        "planner_schedule",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=True),
        sa.Column("task_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("schedule_type", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["planner_history.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["planner_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planner_schedule_user_id"), "planner_schedule", ["user_id"], unique=False)
    op.create_index(op.f("ix_planner_schedule_start_at"), "planner_schedule", ["start_at"], unique=False)

    op.create_table(
        "planner_notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=True),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="info", nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["planner_history.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planner_notifications_user_id"), "planner_notifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_planner_notifications_notification_type"), "planner_notifications", ["notification_type"], unique=False)
    op.create_index(op.f("ix_planner_notifications_is_read"), "planner_notifications", ["is_read"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_planner_notifications_is_read"), table_name="planner_notifications")
    op.drop_index(op.f("ix_planner_notifications_notification_type"), table_name="planner_notifications")
    op.drop_index(op.f("ix_planner_notifications_user_id"), table_name="planner_notifications")
    op.drop_table("planner_notifications")
    op.drop_index(op.f("ix_planner_schedule_start_at"), table_name="planner_schedule")
    op.drop_index(op.f("ix_planner_schedule_user_id"), table_name="planner_schedule")
    op.drop_table("planner_schedule")
    op.drop_index(op.f("ix_planner_tasks_status"), table_name="planner_tasks")
    op.drop_index(op.f("ix_planner_tasks_scheduled_date"), table_name="planner_tasks")
    op.drop_index(op.f("ix_planner_tasks_plan_id"), table_name="planner_tasks")
    op.drop_index(op.f("ix_planner_tasks_user_id"), table_name="planner_tasks")
    op.drop_table("planner_tasks")
    op.drop_index(op.f("ix_planner_history_cache_key"), table_name="planner_history")
    op.drop_index(op.f("ix_planner_history_user_id"), table_name="planner_history")
    op.drop_table("planner_history")
