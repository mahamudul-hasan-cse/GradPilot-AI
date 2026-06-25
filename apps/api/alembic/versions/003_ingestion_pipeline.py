"""Ingestion pipeline schema

Revision ID: 003_ingestion
Revises: 002_discovery
Create Date: 2026-06-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "003_ingestion"
down_revision: Union[str, None] = "002_discovery"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("universities", sa.Column("source_url", sa.String(length=1000), nullable=True))
    op.add_column("universities", sa.Column("external_id", sa.String(length=255), nullable=True))
    op.add_column("universities", sa.Column("last_ingested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("universities", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("universities", sa.Column("data_quality_score", sa.Numeric(precision=5, scale=2), nullable=True))
    op.create_index(op.f("ix_universities_external_id"), "universities", ["external_id"], unique=False)
    op.create_index(op.f("ix_universities_content_hash"), "universities", ["content_hash"], unique=False)

    op.add_column("scholarships", sa.Column("university_id", sa.UUID(), nullable=True))
    op.add_column("scholarships", sa.Column("source_url", sa.String(length=1000), nullable=True))
    op.add_column("scholarships", sa.Column("external_id", sa.String(length=255), nullable=True))
    op.create_foreign_key(
        "fk_scholarships_university_id",
        "scholarships",
        "universities",
        ["university_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_scholarships_university_id"), "scholarships", ["university_id"], unique=False)

    op.create_table(
        "ingestion_sources",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("university_id", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("last_scraped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scrape_interval_hours", sa.Integer(), nullable=False, server_default="168"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_url", name="uq_ingestion_sources_url"),
    )
    op.create_index(op.f("ix_ingestion_sources_source_url"), "ingestion_sources", ["source_url"], unique=False)
    op.create_index(op.f("ix_ingestion_sources_country"), "ingestion_sources", ["country"], unique=False)
    op.create_index(op.f("ix_ingestion_sources_external_id"), "ingestion_sources", ["external_id"], unique=False)
    op.create_index(op.f("ix_ingestion_sources_university_id"), "ingestion_sources", ["university_id"], unique=False)

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("triggered_by", sa.String(length=50), server_default="scheduler", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_sources", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("succeeded", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skipped", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duplicates_merged", sa.Integer(), server_default="0", nullable=False),
        sa.Column("embeddings_indexed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("metrics", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestion_jobs_job_type"), "ingestion_jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_ingestion_jobs_status"), "ingestion_jobs", ["status"], unique=False)

    op.create_table(
        "ingestion_job_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("university_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("stage", sa.String(length=50), nullable=True),
        sa.Column("quality_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("duplicate_of_id", sa.UUID(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("raw_payload", JSON(), nullable=True),
        sa.Column("normalized_payload", JSON(), nullable=True),
        sa.Column("validation_report", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["duplicate_of_id"], ["universities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["ingestion_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["ingestion_sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestion_job_items_job_id"), "ingestion_job_items", ["job_id"], unique=False)
    op.create_index(op.f("ix_ingestion_job_items_status"), "ingestion_job_items", ["status"], unique=False)

    op.create_table(
        "university_fingerprints",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("university_id", sa.UUID(), nullable=False),
        sa.Column("fingerprint_hash", sa.String(length=64), nullable=False),
        sa.Column("normalized_name", sa.String(length=500), nullable=False),
        sa.Column("website_domain", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint_hash", name="uq_university_fingerprints_hash"),
        sa.UniqueConstraint("university_id"),
    )
    op.create_index(op.f("ix_university_fingerprints_fingerprint_hash"), "university_fingerprints", ["fingerprint_hash"], unique=False)
    op.create_index(op.f("ix_university_fingerprints_normalized_name"), "university_fingerprints", ["normalized_name"], unique=False)
    op.create_index(op.f("ix_university_fingerprints_website_domain"), "university_fingerprints", ["website_domain"], unique=False)
    op.create_index(op.f("ix_university_fingerprints_country"), "university_fingerprints", ["country"], unique=False)


def downgrade() -> None:
    op.drop_table("university_fingerprints")
    op.drop_table("ingestion_job_items")
    op.drop_table("ingestion_jobs")
    op.drop_table("ingestion_sources")
    op.drop_index(op.f("ix_scholarships_university_id"), table_name="scholarships")
    op.drop_constraint("fk_scholarships_university_id", "scholarships", type_="foreignkey")
    op.drop_column("scholarships", "external_id")
    op.drop_column("scholarships", "source_url")
    op.drop_column("scholarships", "university_id")
    op.drop_index(op.f("ix_universities_content_hash"), table_name="universities")
    op.drop_index(op.f("ix_universities_external_id"), table_name="universities")
    op.drop_column("universities", "data_quality_score")
    op.drop_column("universities", "content_hash")
    op.drop_column("universities", "last_ingested_at")
    op.drop_column("universities", "external_id")
    op.drop_column("universities", "source_url")
