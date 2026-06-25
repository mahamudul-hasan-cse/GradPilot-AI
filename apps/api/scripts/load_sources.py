"""Load ingestion source catalog into PostgreSQL."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.ingestion import IngestionSource

DEFAULT_CATALOG = Path(__file__).resolve().parent.parent / "data" / "sources" / "universities.json"


async def load_sources(catalog_path: Path, *, dry_run: bool = False) -> int:
    with catalog_path.open(encoding="utf-8") as f:
        records = json.load(f)

    loaded = 0
    async with AsyncSessionLocal() as session:
        for record in records:
            existing = await session.execute(
                select(IngestionSource).where(IngestionSource.source_url == record["source_url"])
            )
            if existing.scalar_one_or_none():
                continue
            if not dry_run:
                session.add(IngestionSource(**record))
            loaded += 1
        if not dry_run:
            await session.commit()
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Load university source catalog")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    count = asyncio.run(load_sources(args.catalog, dry_run=args.dry_run))
    print(f"{'Would load' if args.dry_run else 'Loaded'} {count} ingestion sources.")


if __name__ == "__main__":
    main()
