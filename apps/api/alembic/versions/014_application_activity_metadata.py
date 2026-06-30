"""Application activity metadata column fix

Revision ID: 014_app_activity_meta
Revises: 013_feature_runtime_fixes
Create Date: 2026-06-30

"""

from typing import Sequence, Union

from alembic import op

revision: str = "014_app_activity_meta"
down_revision: Union[str, None] = "013_feature_runtime_fixes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'application_activity' AND column_name = 'event_metadata'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'application_activity' AND column_name = 'metadata'
            ) THEN
                ALTER TABLE application_activity RENAME COLUMN event_metadata TO metadata;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'application_activity' AND column_name = 'metadata'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'application_activity' AND column_name = 'event_metadata'
            ) THEN
                ALTER TABLE application_activity RENAME COLUMN metadata TO event_metadata;
            END IF;
        END $$;
        """
    )
