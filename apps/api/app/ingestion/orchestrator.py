"""Ingestion pipeline orchestrator — coordinates all stages."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.deduplicator import UniversityDeduplicator
from app.ingestion.extractor import UniversityExtractor
from app.ingestion.loaders import PostgresLoader, QdrantLoader
from app.ingestion.normalizer import UniversityNormalizer
from app.ingestion.scraper import UniversityScraper
from app.ingestion.validator import DataQualityValidator
from app.models.ingestion import IngestionJob, IngestionJobItem, IngestionSource

from app.models.university import University


logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.extractor = UniversityExtractor()
        self.normalizer = UniversityNormalizer()
        self.validator = DataQualityValidator()
        self.deduplicator = UniversityDeduplicator(db)
        self.postgres_loader = PostgresLoader(db)
        self.qdrant_loader = QdrantLoader()

    async def create_job(self, job_type: str, triggered_by: str = "scheduler") -> IngestionJob:
        job = IngestionJob(job_type=job_type, status="pending", triggered_by=triggered_by)
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_stale_sources(self, limit: int = 100) -> list[IngestionSource]:
        now = datetime.now(UTC)
        stmt = (
            select(IngestionSource)
            .where(IngestionSource.is_active.is_(True))
            .order_by(IngestionSource.priority.asc(), IngestionSource.last_scraped_at.asc().nullsfirst())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        sources = list(result.scalars().all())
        stale = []
        for source in sources:
            if source.last_scraped_at is None:
                stale.append(source)
                continue
            hours = (now - source.last_scraped_at).total_seconds() / 3600
            if hours >= source.scrape_interval_hours:
                stale.append(source)
        return stale

    async def run_job(
        self,
        job: IngestionJob,
        sources: list[IngestionSource],
        *,
        skip_embedding: bool = False,
    ) -> IngestionJob:
        job.status = "running"
        job.started_at = datetime.now(UTC)
        job.total_sources = len(sources)
        await self.db.flush()

        indexed_universities = []

        async with UniversityScraper() as scraper:
            for source in sources:
                item = IngestionJobItem(job_id=job.id, source_id=source.id, status="running")
                self.db.add(item)
                await self.db.flush()

                try:
                    await self._process_source(scraper, source, item, skip_embedding=skip_embedding)
                    job.processed += 1
                    if item.status == "succeeded":
                        job.succeeded += 1
                        if item.university_id and not skip_embedding:
                            uni = await self.db.get(University, item.university_id)
                            if uni:
                                indexed_universities.append(uni)
                    elif item.status == "skipped":
                        job.skipped += 1
                        if item.is_duplicate:
                            job.duplicates_merged += 1
                    else:
                        job.failed += 1
                except Exception as exc:
                    logger.exception("Ingestion failed for %s", source.source_url)
                    item.status = "failed"
                    item.error_message = str(exc)
                    job.failed += 1
                    job.processed += 1
                    source.consecutive_failures += 1

                source.last_scraped_at = datetime.now(UTC)
                if item.status == "succeeded":
                    source.last_success_at = datetime.now(UTC)
                    source.consecutive_failures = 0

        if indexed_universities and not skip_embedding:
            job.embeddings_indexed = self.qdrant_loader.index_batch(indexed_universities)

        job.status = "completed" if job.failed == 0 else "completed_with_errors"
        job.completed_at = datetime.now(UTC)
        job.metrics = {
            "success_rate": round(job.succeeded / max(job.processed, 1) * 100, 2),
            "embeddings_indexed": job.embeddings_indexed,
        }
        await self.db.flush()
        return job

    async def _process_source(
        self,
        scraper: UniversityScraper,
        source: IngestionSource,
        item: IngestionJobItem,
        *,
        skip_embedding: bool,
    ) -> None:
        item.stage = "scrape"
        scrape = await scraper.fetch(source.source_url)
        if scrape.error or not scrape.html:
            item.status = "failed"
            item.error_message = scrape.error or "Empty response"
            return

        item.stage = "extract"
        extracted = self.extractor.extract(
            scrape,
            fallback_name=source.name,
            fallback_country=source.country,
        )
        item.raw_payload = extracted.model_dump(mode="json")

        item.stage = "normalize"
        normalized = self.normalizer.normalize(
            extracted,
            source_url=source.source_url,
            external_id=source.external_id,
            fallback_country=source.country,
        )
        item.normalized_payload = normalized.model_dump(mode="json")

        item.stage = "validate"
        validation = self.validator.validate(normalized)
        item.validation_report = validation.model_dump(mode="json")
        item.quality_score = validation.score

        if not validation.passed:
            item.status = "failed"
            item.error_message = "Quality validation failed"
            return

        item.stage = "dedup"
        dedup = await self.deduplicator.check_duplicate(normalized)
        if dedup.is_duplicate and dedup.duplicate_of_id:
            item.status = "skipped"
            item.is_duplicate = True
            item.duplicate_of_id = dedup.duplicate_of_id
            item.stage = "dedup_merged"
            university = await self.postgres_loader.upsert_university(
                normalized,
                quality_score=validation.score,
                existing_id=dedup.duplicate_of_id,
            )
            item.university_id = university.id
            source.university_id = university.id
            return

        item.stage = "load"
        university = await self.postgres_loader.upsert_university(
            normalized,
            quality_score=validation.score,
            existing_id=source.university_id,
        )
        item.university_id = university.id
        source.university_id = university.id

        await self.deduplicator.register_fingerprint(university.id, normalized)

        if not skip_embedding:
            item.stage = "embed"
            self.qdrant_loader.index_university(university)

        item.status = "succeeded"
        item.stage = "complete"

    async def run_incremental(self, *, batch_size: int = 50, triggered_by: str = "scheduler") -> IngestionJob:
        sources = await self.get_stale_sources(limit=batch_size)
        job = await self.create_job("incremental", triggered_by=triggered_by)
        return await self.run_job(job, sources)

    async def run_full(self, *, batch_size: int = 200, triggered_by: str = "scheduler") -> IngestionJob:
        stmt = (
            select(IngestionSource)
            .where(IngestionSource.is_active.is_(True))
            .order_by(IngestionSource.priority.asc())
            .limit(batch_size)
        )
        result = await self.db.execute(stmt)
        sources = list(result.scalars().all())
        job = await self.create_job("full", triggered_by=triggered_by)
        return await self.run_job(job, sources)

    async def get_dashboard_metrics(self) -> dict:
        total_sources = await self.db.scalar(select(func.count()).select_from(IngestionSource))
        active_sources = await self.db.scalar(
            select(func.count()).select_from(IngestionSource).where(IngestionSource.is_active.is_(True))
        )
        total_universities = await self.db.scalar(select(func.count()).select_from(University))
        avg_quality = await self.db.scalar(select(func.avg(University.data_quality_score)))

        recent_jobs = await self.db.execute(
            select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(10)
        )
        jobs = recent_jobs.scalars().all()

        failed_sources = await self.db.scalar(
            select(func.count())
            .select_from(IngestionSource)
            .where(IngestionSource.consecutive_failures >= 3)
        )

        return {
            "total_sources": total_sources or 0,
            "active_sources": active_sources or 0,
            "total_universities": total_universities or 0,
            "avg_quality_score": round(float(avg_quality or 0), 2),
            "failed_sources": failed_sources or 0,
            "recent_jobs": [
                {
                    "id": str(j.id),
                    "job_type": j.job_type,
                    "status": j.status,
                    "processed": j.processed,
                    "succeeded": j.succeeded,
                    "failed": j.failed,
                    "duplicates_merged": j.duplicates_merged,
                    "embeddings_indexed": j.embeddings_indexed,
                    "started_at": j.started_at.isoformat() if j.started_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                }
                for j in jobs
            ],
        }
