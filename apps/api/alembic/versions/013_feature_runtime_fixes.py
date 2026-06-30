"""Feature runtime schema fixes

Revision ID: 013_feature_runtime_fixes
Revises: 012_sop_studio
Create Date: 2026-06-30

"""

from typing import Sequence, Union

from alembic import op

revision: str = "013_feature_runtime_fixes"
down_revision: Union[str, None] = "012_sop_studio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'twin_timeline' AND column_name = 'entry_metadata'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'twin_timeline' AND column_name = 'metadata'
            ) THEN
                ALTER TABLE twin_timeline RENAME COLUMN entry_metadata TO metadata;
            END IF;
        END $$;
        """
    )

    for table_name in (
        "recommendation_history",
        "scholarship_recommendation_history",
        "profile_analysis",
        "planner_history",
    ):
        op.execute(f"ALTER TABLE {table_name} ALTER COLUMN cache_key TYPE VARCHAR(128)")


def downgrade() -> None:
    for table_name in (
        "recommendation_history",
        "scholarship_recommendation_history",
        "profile_analysis",
        "planner_history",
    ):
        op.execute(f"ALTER TABLE {table_name} ALTER COLUMN cache_key TYPE VARCHAR(64)")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'twin_timeline' AND column_name = 'metadata'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'twin_timeline' AND column_name = 'entry_metadata'
            ) THEN
                ALTER TABLE twin_timeline RENAME COLUMN metadata TO entry_metadata;
            END IF;
        END $$;
        """
    )
