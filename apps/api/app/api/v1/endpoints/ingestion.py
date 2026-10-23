from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin_user
from app.db.session import AsyncSessionLocal, get_db
from app.ingestion.orchestrator import IngestionOrchestrator
from app.ingestion.url_safety import UnsafeURLError, validate_public_url
from app.models.ingestion import IngestionJob, IngestionSource
from app.schemas.ingestion import (
    IngestionDashboardResponse,
    IngestionJobResponse,
    IngestionSourceCreate,
    IngestionSourceResponse,
    TriggerJobRequest,
)

router = APIRouter(
    prefix="/ingestion",
    tags=["Data Ingestion"],
    dependencies=[Depends(get_current_admin_user)],
)


async def _run_job_background(job_type: str, batch_size: int | None) -> None:
    async with AsyncSessionLocal() as session:
        orchestrator = IngestionOrchestrator(session)
        try:
            if job_type == "full":
                await orchestrator.run_full(
                    batch_size=batch_size or 200,
                    triggered_by="api",
                )
            else:
                await orchestrator.run_incremental(
                    batch_size=batch_size or 50,
                    triggered_by="api",
                )
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.get("/dashboard", response_model=IngestionDashboardResponse)
async def get_ingestion_dashboard(db: AsyncSession = Depends(get_db)) -> IngestionDashboardResponse:
    orchestrator = IngestionOrchestrator(db)
    metrics = await orchestrator.get_dashboard_metrics()
    return IngestionDashboardResponse(**metrics)


@router.get("/jobs", response_model=list[IngestionJobResponse])
async def list_ingestion_jobs(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[IngestionJobResponse]:
    result = await db.execute(
        select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(limit)
    )
    jobs = result.scalars().all()
    return [IngestionJobResponse.model_validate(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
async def get_ingestion_job(job_id: UUID, db: AsyncSession = Depends(get_db)) -> IngestionJobResponse:
    job = await db.get(IngestionJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return IngestionJobResponse.model_validate(job)


@router.post("/jobs/trigger", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingestion_job(
    request: TriggerJobRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    background_tasks.add_task(_run_job_background, request.job_type, request.batch_size)
    return {
        "message": f"{request.job_type} ingestion job queued",
        "job_type": request.job_type,
        "batch_size": request.batch_size,
    }


@router.get("/sources", response_model=list[IngestionSourceResponse])
async def list_ingestion_sources(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[IngestionSourceResponse]:
    result = await db.execute(
        select(IngestionSource).order_by(IngestionSource.priority.asc()).limit(limit)
    )
    return [IngestionSourceResponse.model_validate(s) for s in result.scalars().all()]


@router.post("/sources", response_model=IngestionSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_ingestion_source(
    data: IngestionSourceCreate,
    db: AsyncSession = Depends(get_db),
) -> IngestionSourceResponse:
    try:
        await validate_public_url(data.source_url)
    except UnsafeURLError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    existing = await db.execute(
        select(IngestionSource).where(IngestionSource.source_url == data.source_url)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Source URL already exists")

    source = IngestionSource(**data.model_dump())
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return IngestionSourceResponse.model_validate(source)
