"""Redis-backed conversation memory with PostgreSQL persistence."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

import redis.asyncio as redis

from app.core.config import settings
from app.services.knowledge.types import ChatMessage

logger = logging.getLogger(__name__)


class ConversationMemory:
    PREFIX = "knowledge:memory:"
    MAX_TURNS = 20
    TTL_SECONDS = 86400

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
                logger.warning("Redis memory unavailable: %s", exc)
                self._enabled = False
                return None
        return self._client

    def _key(self, session_id: UUID) -> str:
        return f"{self.PREFIX}{session_id}"

    async def get_messages(self, session_id: UUID) -> list[ChatMessage]:
        client = await self._get_client()
        if client is None:
            return []
        try:
            raw = await client.get(self._key(session_id))
            if not raw:
                return []
            data = json.loads(raw)
            return [ChatMessage(**m) for m in data]
        except Exception as exc:
            logger.warning("Memory get failed: %s", exc)
            return []

    async def append(self, session_id: UUID, message: ChatMessage) -> None:
        messages = await self.get_messages(session_id)
        messages.append(message)
        messages = messages[-self.MAX_TURNS :]
        client = await self._get_client()
        if client is None:
            return
        try:
            await client.setex(
                self._key(session_id),
                self.TTL_SECONDS,
                json.dumps([self._serialize(m) for m in messages]),
            )
        except Exception as exc:
            logger.warning("Memory append failed: %s", exc)

    async def set_messages(self, session_id: UUID, messages: list[ChatMessage]) -> None:
        client = await self._get_client()
        if client is None:
            return
        try:
            await client.setex(
                self._key(session_id),
                self.TTL_SECONDS,
                json.dumps([self._serialize(m) for m in messages[-self.MAX_TURNS :]]),
            )
        except Exception as exc:
            logger.warning("Memory set failed: %s", exc)

    def format_history(self, messages: list[ChatMessage], *, last_n: int = 6) -> str:
        lines: list[str] = []
        for msg in messages[-last_n:]:
            role = msg.role.capitalize()
            lines.append(f"{role}: {msg.content[:500]}")
        return "\n".join(lines)

    @staticmethod
    def _serialize(message: ChatMessage) -> dict[str, Any]:
        return {
            "role": message.role,
            "content": message.content,
            "citations": message.citations,
        }

    @staticmethod
    def to_db_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
        return [ConversationMemory._serialize(m) for m in messages]
