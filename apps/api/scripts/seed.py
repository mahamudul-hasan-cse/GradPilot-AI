"""Seed sample universities and scholarships for local development."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.seed_universities import load_seed_data


async def seed() -> None:
    await load_seed_data(force=False, index_vectors=True)


if __name__ == "__main__":
    asyncio.run(seed())
