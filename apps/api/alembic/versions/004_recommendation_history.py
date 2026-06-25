"""Recommendation history table

Revision ID: 004_recommendations
Revises: 003_ingestion
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "004_recommendations"
down_revision: Union[str, None] = "003_ingestion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("cache_key", sa.String(length=64), nullable=True),
        sa.Column("request_payload", JSON(), nullable=False),
        sa.Column("response_summary", JSON(), nullable=False),
        sa.Column("total_score_avg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("safe_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("target_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ambitious_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("candidates_evaluated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cache_hit", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendation_history_user_id"), "recommendation_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_recommendation_history_cache_key"), "recommendation_history", ["cache_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_recommendation_history_cache_key"), table_name="recommendation_history")
    op.drop_index(op.f("ix_recommendation_history_user_id"), table_name="recommendation_history")
    op.drop_table("recommendation_history")
