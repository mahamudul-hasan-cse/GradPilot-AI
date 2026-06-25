"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="student"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "universities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("ranking", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_universities_country"), "universities", ["country"], unique=False)
    op.create_index(op.f("ix_universities_name"), "universities", ["name"], unique=False)

    op.create_table(
        "scholarships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True, server_default="USD"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("eligibility", sa.Text(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("application_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scholarships_country"), "scholarships", ["country"], unique=False)
    op.create_index(op.f("ix_scholarships_title"), "scholarships", ["title"], unique=False)

    op.create_table(
        "student_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("nationality", sa.String(length=100), nullable=True),
        sa.Column("current_country", sa.String(length=100), nullable=True),
        sa.Column("education_level", sa.String(length=100), nullable=True),
        sa.Column("field_of_study", sa.String(length=255), nullable=True),
        sa.Column("gpa", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("gpa_scale", sa.Numeric(precision=4, scale=2), nullable=True, server_default="4.0"),
        sa.Column("target_degree", sa.String(length=100), nullable=True),
        sa.Column("target_countries", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("budget_min", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("budget_max", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("budget_currency", sa.String(length=10), nullable=True, server_default="USD"),
        sa.Column("test_scores", sa.JSON(), nullable=True),
        sa.Column("work_experience_years", sa.Integer(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "programs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("university_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("degree_type", sa.String(length=50), nullable=False),
        sa.Column("field_of_study", sa.String(length=255), nullable=True),
        sa.Column("duration_months", sa.Integer(), nullable=True),
        sa.Column("tuition_fee", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("tuition_currency", sa.String(length=10), nullable=True, server_default="USD"),
        sa.Column("language", sa.String(length=50), nullable=True, server_default="English"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirements", sa.JSON(), nullable=True),
        sa.Column("application_deadline", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_programs_degree_type"), "programs", ["degree_type"], unique=False)
    op.create_index(op.f("ix_programs_name"), "programs", ["name"], unique=False)

    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("program_id", sa.UUID(), nullable=True),
        sa.Column("university_id", sa.UUID(), nullable=True),
        sa.Column("scholarship_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["scholarship_id"], ["scholarships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_applications_status"), "applications", ["status"], unique=False)

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("session_type", sa.String(length=50), nullable=False, server_default="guidance"),
        sa.Column("messages", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("chat_sessions")
    op.drop_index(op.f("ix_applications_status"), table_name="applications")
    op.drop_table("applications")
    op.drop_index(op.f("ix_programs_name"), table_name="programs")
    op.drop_index(op.f("ix_programs_degree_type"), table_name="programs")
    op.drop_table("programs")
    op.drop_table("student_profiles")
    op.drop_index(op.f("ix_scholarships_title"), table_name="scholarships")
    op.drop_index(op.f("ix_scholarships_country"), table_name="scholarships")
    op.drop_table("scholarships")
    op.drop_index(op.f("ix_universities_name"), table_name="universities")
    op.drop_index(op.f("ix_universities_country"), table_name="universities")
    op.drop_table("universities")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
