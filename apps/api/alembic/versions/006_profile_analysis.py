"""Profile analysis history table

Revision ID: 006_profile_analysis
Revises: 005_scholarship_matching
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "006_profile_analysis"
down_revision: Union[str, None] = "005_scholarship_matching"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "profile_analysis",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("cache_key", sa.String(length=64), nullable=True),
        sa.Column("analyzer_type", sa.String(length=50), server_default="rule_based", nullable=False),
        sa.Column("request_payload", JSON(), nullable=False),
        sa.Column("response_summary", JSON(), nullable=False),
        sa.Column("admission_readiness_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("scholarship_readiness_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("employability_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("recommended_university_tier", sa.String(length=100), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_profile_analysis_user_id"), "profile_analysis", ["user_id"], unique=False)
    op.create_index(op.f("ix_profile_analysis_cache_key"), "profile_analysis", ["cache_key"], unique=False)
    op.create_index(
        op.f("ix_profile_analysis_analyzer_type"), "profile_analysis", ["analyzer_type"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_profile_analysis_analyzer_type"), table_name="profile_analysis")
    op.drop_index(op.f("ix_profile_analysis_cache_key"), table_name="profile_analysis")
    op.drop_index(op.f("ix_profile_analysis_user_id"), table_name="profile_analysis")
    op.drop_table("profile_analysis")
