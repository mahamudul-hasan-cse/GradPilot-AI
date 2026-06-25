# Data Ingestion Pipeline

GradPilot AI ingests university data at scale (10,000+ institutions) through a multi-stage pipeline.

## Architecture

```
Source Catalog (JSON/API)
        │
        ▼
┌───────────────┐     ┌────────────┐     ┌─────────────┐
│  1. Scrape    │────▶│ 2. Extract │────▶│ 3. Normalize│
│  (httpx)      │     │ (BS4+JSON) │     │ (canonical) │
└───────────────┘     └────────────┘     └──────┬──────┘
                                               │
        ┌──────────────────────────────────────┤
        ▼                                      ▼
┌───────────────┐     ┌────────────┐     ┌─────────────┐
│ 4. Validate   │────▶│ 5. Dedup   │────▶│ 6. Postgres │
│ (quality)     │     │ (hash/fuzzy)│     │   loader    │
└───────────────┘     └────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ 7. Qdrant   │
                                        │ (embeddings)│
                                        └─────────────┘
```

## Pipeline Stages

| Stage | Module | Output |
|-------|--------|--------|
| Scrape | `ingestion/scraper.py` | Raw HTML with rate limiting |
| Extract | `ingestion/extractor.py` | Programs, tuition, deadlines, requirements, scholarships |
| Normalize | `ingestion/normalizer.py` | Canonical schema + content hash |
| Validate | `ingestion/validator.py` | Quality score 0–100 |
| Dedup | `ingestion/deduplicator.py` | Hash, domain, fuzzy (rapidfuzz) matching |
| Load | `ingestion/loaders.py` | PostgreSQL + Qdrant |

## Scheduled Jobs

| Job | Default Schedule | Batch Size |
|-----|------------------|------------|
| Incremental | Every 6 hours (`0 */6 * * *`) | 50 stale sources |
| Full | Weekly Sunday 2am (`0 2 * * 0`) | 200 sources |

Run via the **worker** service:

```bash
docker compose up worker -d
```

## Quick Start

```bash
# 1. Apply migration
docker compose exec api alembic upgrade head

# 2. Load source catalog (20 universities)
docker compose exec api python scripts/load_sources.py

# 3. Run ingestion manually
docker compose exec api python -c "
import asyncio
from app.db.session import AsyncSessionLocal
from app.ingestion.orchestrator import IngestionOrchestrator

async def run():
    async with AsyncSessionLocal() as s:
        o = IngestionOrchestrator(s)
        job = await o.run_incremental(batch_size=5, triggered_by='manual')
        await s.commit()
        print(f'Job {job.id}: {job.succeeded}/{job.processed} succeeded')

asyncio.run(run())
"

# 4. View dashboard
open http://localhost:3000/admin/ingestion
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ingestion/dashboard` | Monitoring metrics |
| GET | `/api/v1/ingestion/jobs` | Recent job history |
| POST | `/api/v1/ingestion/jobs/trigger` | Trigger incremental/full job |
| GET | `/api/v1/ingestion/sources` | List source catalog |
| POST | `/api/v1/ingestion/sources` | Add new source URL |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INGESTION_CONCURRENCY` | 10 | Max parallel scrapes |
| `INGESTION_RATE_LIMIT_PER_DOMAIN` | 1.0 | Requests/sec per domain |
| `INGESTION_BATCH_SIZE` | 50 | Incremental batch size |
| `INGESTION_INCREMENTAL_CRON` | `0 */6 * * *` | Incremental schedule |
| `INGESTION_FULL_CRON` | `0 2 * * 0` | Full refresh schedule |
| `INGESTION_RESPECT_ROBOTS` | true | Honor robots.txt |

## Scaling to 10,000+ Universities

- **Source catalog** table indexes URLs; add sources via API or bulk JSON import
- **Batch processing** with configurable concurrency and per-domain rate limits
- **Incremental updates** only re-scrape stale sources (default: 7-day interval)
- **Deduplication index** (`university_fingerprints`) prevents duplicate records
- **Content hashing** skips unnecessary re-processing when data unchanged
- **Separate worker** process decouples ingestion from API serving

## Data Quality

Validation scores each record 0–100 based on:
- Required fields: name, country, website, source_url
- Important fields: tuition, GPA, IELTS, deadline, programs, description
- Errors (-25 each): missing required fields, invalid values
- Warnings (-5 each): missing recommended fields

Records scoring below 50 or with errors are rejected.

## Tests

```bash
cd apps/api
pytest tests/test_ingestion_pipeline.py -v
```
