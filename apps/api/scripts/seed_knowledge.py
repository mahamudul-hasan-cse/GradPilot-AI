"""Seed and index the GradPilot knowledge base."""

import argparse
import asyncio

from app.db.session import AsyncSessionLocal
from app.services.knowledge.indexer import KnowledgeIndexer


async def run_index() -> None:
    async with AsyncSessionLocal() as session:
        indexer = KnowledgeIndexer(session)
        counts = await indexer.index_all()
        await session.commit()
        print(f"Knowledge base indexed: {counts}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Index GradPilot knowledge base")
    parser.parse_args()
    asyncio.run(run_index())


if __name__ == "__main__":
    main()
