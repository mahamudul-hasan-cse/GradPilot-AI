"""Async document processing queue with Redis backing."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

QUEUE_KEY = "docintel:queue"


class DocumentProcessingQueue:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._enabled = settings.redis_enabled

    async def _get_client(self) -> redis.Redis | None:
        if not self._enabled:
            return None
        if self._client is None:
            try:
                self._client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
                await self._client.ping()
            except Exception as exc:
                logger.warning("Document queue Redis unavailable: %s", exc)
                self._enabled = False
                return None
        return self._client

    async def enqueue(self, job_id: UUID, document_id: UUID, user_id: UUID) -> int | None:
        client = await self._get_client()
        payload = json.dumps({
            "job_id": str(job_id),
            "document_id": str(document_id),
            "user_id": str(user_id),
            "enqueued_at": datetime.now(UTC).isoformat(),
        })
        if client:
            await client.rpush(QUEUE_KEY, payload)
            return await client.llen(QUEUE_KEY)
        return None

    async def dequeue(self) -> dict | None:
        client = await self._get_client()
        if client is None:
            return None
        raw = await client.lpop(QUEUE_KEY)
        if raw:
            return json.loads(raw)
        return None

    async def queue_length(self) -> int:
        client = await self._get_client()
        if client is None:
            return 0
        return await client.llen(QUEUE_KEY) or 0
