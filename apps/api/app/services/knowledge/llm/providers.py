"""Compatibility shim for the Gemini-only AI service."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.services.ai.gemini_service import GeminiService


class LLMProvider(ABC):
    provider_name: str

    @abstractmethod
    async def generate(self, *, system: str, user: str, temperature: float = 0.2) -> str:
        pass

    @abstractmethod
    async def stream(self, *, system: str, user: str, temperature: float = 0.2) -> AsyncIterator[str]:
        pass

    @property
    def is_available(self) -> bool:
        return True


class GeminiLLMProvider(LLMProvider):
    """Legacy provider interface backed by the single GeminiService."""

    provider_name = "gemini"

    def __init__(self) -> None:
        self.service = GeminiService()

    @property
    def is_available(self) -> bool:
        return self.service.is_available

    async def generate(self, *, system: str, user: str, temperature: float = 0.2) -> str:
        return await self.service.generate_text(user, system=system, temperature=temperature)

    async def stream(self, *, system: str, user: str, temperature: float = 0.2) -> AsyncIterator[str]:
        async for chunk in self.service.stream_text(user, system=system, temperature=temperature):
            yield chunk


def get_llm_provider(provider: str | None = None) -> LLMProvider:
    # Keep the old function signature so existing endpoints and engines do not break.
    # Provider selection is intentionally ignored: Gemini is the only generative AI engine.
    return GeminiLLMProvider()
