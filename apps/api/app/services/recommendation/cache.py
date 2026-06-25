"""Redis cache for recommendation responses."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RecommendationCache:
    def __init__(self, client: redis.Redis | None = None, *, prefix: str = "rec:universities:") -> None:
        self._client = client
        self._enabled = settings.redis_enabled
        self.prefix = prefix

    async def _get_client(self) -> redis.Redis | None:
        if not self._enabled:
            return None
        if self._client is None:
            try:
                self._client = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._client.ping()
            except Exception as exc:
                logger.warning("Redis unavailable, caching disabled: %s", exc)
                self._enabled = False
                return None
        return self._client

    def build_cache_key(self, payload: dict[str, Any]) -> str:
        normalized = json.dumps(payload, sort_keys=True, default=str)
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        return f"{self.prefix}{digest}"

    async def get(self, cache_key: str) -> dict[str, Any] | None:
        client = await self._get_client()
        if client is None:
            return None
        try:
            raw = await client.get(cache_key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.warning("Redis get failed: %s", exc)
        return None

    async def set(self, cache_key: str, value: dict[str, Any]) -> None:
        client = await self._get_client()
        if client is None:
            return
        try:
            await client.setex(
                cache_key,
                settings.recommendation_cache_ttl_seconds,
                json.dumps(value, default=str),
            )
        except Exception as exc:
            logger.warning("Redis set failed: %s", exc)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
