"""Scholarship matching fields and recommendation history

Revision ID: 005_scholarship_matching
Revises: 004_recommendations
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSON

revision: str = "005_scholarship_matching"
down_revision: Union[str, None] = "004_recommendations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scholarships", sa.Column("degree_level", sa.String(length=50), nullable=True))
    op.add_column("scholarships", sa.Column("funding_type", sa.String(length=50), nullable=True))
    op.add_column("scholarships", sa.Column("minimum_gpa", sa.Numeric(precision=4, scale=2), nullable=True))
    op.add_column("scholarships", sa.Column("minimum_ielts", sa.Numeric(precision=3, scale=1), nullable=True))
    op.add_column(
        "scholarships",
        sa.Column("research_required", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("scholarships", sa.Column("work_experience_required_years", sa.Integer(), nullable=True))
    op.add_column("scholarships", sa.Column("eligible_nationalities", ARRAY(sa.String()), nullable=True))
    op.add_column("scholarships", sa.Column("eligible_majors", ARRAY(sa.String()), nullable=True))
    op.create_index(op.f("ix_scholarships_degree_level"), "scholarships", ["degree_level"], unique=False)
    op.create_index(op.f("ix_scholarships_funding_type"), "scholarships", ["funding_type"], unique=False)
    op.create_index(op.f("ix_scholarships_minimum_gpa"), "scholarships", ["minimum_gpa"], unique=False)

    op.create_table(
        "scholarship_recommendation_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("cache_key", sa.String(length=64), nullable=True),
        sa.Column("request_payload", JSON(), nullable=False),
        sa.Column("response_summary", JSON(), nullable=False),
        sa.Column("avg_scholarship_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("avg_eligibility_probability", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("excellent_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("strong_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("possible_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("low_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("candidates_evaluated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cache_hit", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_scholarship_recommendation_history_user_id"),
        "scholarship_recommendation_history",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scholarship_recommendation_history_cache_key"),
        "scholarship_recommendation_history",
        ["cache_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("scholarship_recommendation_history")
    op.drop_index(op.f("ix_scholarships_minimum_gpa"), table_name="scholarships")
    op.drop_index(op.f("ix_scholarships_funding_type"), table_name="scholarships")
    op.drop_index(op.f("ix_scholarships_degree_level"), table_name="scholarships")
    op.drop_column("scholarships", "eligible_majors")
    op.drop_column("scholarships", "eligible_nationalities")
    op.drop_column("scholarships", "work_experience_required_years")
    op.drop_column("scholarships", "research_required")
    op.drop_column("scholarships", "minimum_ielts")
    op.drop_column("scholarships", "minimum_gpa")
    op.drop_column("scholarships", "funding_type")
    op.drop_column("scholarships", "degree_level")
