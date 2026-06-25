"""Redis-backed event bus with PostgreSQL persistence."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

import redis.asyncio as redis

from app.core.config import settings
from app.services.digital_twin.types import TwinEventMessage

logger = logging.getLogger(__name__)

EventHandler = Callable[[TwinEventMessage], Awaitable[None]]


class EventBus:
    PREFIX = "twin:events:"
    RECENT_TTL = 86400
    MAX_RECENT = 50

    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._enabled = settings.redis_enabled
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    async def _get_client(self) -> redis.Redis | None:
        if not self._enabled:
            return None
        if self._client is None:
            try:
                self._client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
                await self._client.ping()
            except Exception as exc:
                logger.warning("Event bus Redis unavailable: %s", exc)
                self._enabled = False
                return None
        return self._client

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)
        self._subscribers["*"].append(handler)

    async def publish(self, event: TwinEventMessage) -> None:
        client = await self._get_client()
        if client:
            try:
                key = f"{self.PREFIX}{event.user_id}"
                entry = json.dumps({
                    "event_id": str(event.event_id) if event.event_id else None,
                    "event_type": event.event_type,
                    "source_service": event.source_service,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                }, default=str)
                await client.lpush(key, entry)
                await client.ltrim(key, 0, self.MAX_RECENT - 1)
                await client.expire(key, self.RECENT_TTL)
            except Exception as exc:
                logger.warning("Event cache publish failed: %s", exc)

        for handler in self._subscribers.get(event.event_type, []):
            try:
                await handler(event)
            except Exception as exc:
                logger.error("Event handler failed for %s: %s", event.event_type, exc)

        for handler in self._subscribers.get("*", []):
            if handler not in self._subscribers.get(event.event_type, []):
                try:
                    await handler(event)
                except Exception as exc:
                    logger.error("Wildcard handler failed: %s", exc)

    async def get_recent(self, user_id: UUID, *, limit: int = 20) -> list[dict[str, Any]]:
        client = await self._get_client()
        if client is None:
            return []
        try:
            raw_items = await client.lrange(f"{self.PREFIX}{user_id}", 0, limit - 1)
            return [json.loads(item) for item in raw_items]
        except Exception as exc:
            logger.warning("Event cache read failed: %s", exc)
            return []

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
