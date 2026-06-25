"""Scheduled ingestion jobs."""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.ingestion.orchestrator import IngestionOrchestrator

logger = logging.getLogger(__name__)


async def run_incremental_job() -> None:
    logger.info("Starting scheduled incremental ingestion job")
    async with AsyncSessionLocal() as session:
        orchestrator = IngestionOrchestrator(session)
        try:
            job = await orchestrator.run_incremental(
                batch_size=settings.ingestion_batch_size,
                triggered_by="scheduler",
            )
            await session.commit()
            logger.info(
                "Incremental job %s completed: %s succeeded, %s failed",
                job.id,
                job.succeeded,
                job.failed,
            )
        except Exception:
            await session.rollback()
            logger.exception("Scheduled incremental ingestion failed")


async def run_full_job() -> None:
    logger.info("Starting scheduled full ingestion job")
    async with AsyncSessionLocal() as session:
        orchestrator = IngestionOrchestrator(session)
        try:
            job = await orchestrator.run_full(
                batch_size=settings.ingestion_full_batch_size,
                triggered_by="scheduler",
            )
            await session.commit()
            logger.info("Full job %s completed", job.id)
        except Exception:
            await session.rollback()
            logger.exception("Scheduled full ingestion failed")


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_incremental_job,
        CronTrigger.from_crontab(settings.ingestion_incremental_cron),
        id="incremental_ingestion",
        replace_existing=True,
    )
    scheduler.add_job(
        run_full_job,
        CronTrigger.from_crontab(settings.ingestion_full_cron),
        id="full_ingestion",
        replace_existing=True,
    )
    return scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Ingestion worker started. Incremental: %s | Full: %s",
                settings.ingestion_incremental_cron, settings.ingestion_full_cron)
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
