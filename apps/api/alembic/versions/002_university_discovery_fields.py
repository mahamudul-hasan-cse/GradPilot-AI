"""University discovery fields

Revision ID: 002_discovery
Revises: 001_initial
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "002_discovery"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("universities", sa.Column("tuition_fee", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("universities", sa.Column("application_fee", sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column("universities", sa.Column("minimum_gpa", sa.Numeric(precision=4, scale=2), nullable=True))
    op.add_column("universities", sa.Column("minimum_ielts", sa.Numeric(precision=3, scale=1), nullable=True))
    op.add_column("universities", sa.Column("minimum_toefl", sa.Integer(), nullable=True))
    op.add_column("universities", sa.Column("deadline", sa.Date(), nullable=True))
    op.add_column("universities", sa.Column("programs", JSON(), nullable=True))
    op.add_column(
        "universities",
        sa.Column("scholarships_available", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("universities", sa.Column("search_text", sa.Text(), nullable=True))
    op.add_column("universities", sa.Column("majors", sa.ARRAY(sa.String()), nullable=True))

    op.create_index(op.f("ix_universities_ranking"), "universities", ["ranking"], unique=False)
    op.create_index(op.f("ix_universities_tuition_fee"), "universities", ["tuition_fee"], unique=False)
    op.create_index(op.f("ix_universities_minimum_gpa"), "universities", ["minimum_gpa"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_universities_minimum_gpa"), table_name="universities")
    op.drop_index(op.f("ix_universities_tuition_fee"), table_name="universities")
    op.drop_index(op.f("ix_universities_ranking"), table_name="universities")
    op.drop_column("universities", "majors")
    op.drop_column("universities", "search_text")
    op.drop_column("universities", "scholarships_available")
    op.drop_column("universities", "programs")
    op.drop_column("universities", "deadline")
    op.drop_column("universities", "minimum_toefl")
    op.drop_column("universities", "minimum_ielts")
    op.drop_column("universities", "minimum_gpa")
    op.drop_column("universities", "application_fee")
    op.drop_column("universities", "tuition_fee")
