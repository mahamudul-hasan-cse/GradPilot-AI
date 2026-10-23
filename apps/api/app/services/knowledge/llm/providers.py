"""Compatibility shim over the shared generative AI service (OpenRouter or Gemini)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.services.ai import GenerativeService, get_generative_service


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


class GenerativeLLMProvider(LLMProvider):
    """Legacy provider interface backed by the preferred generative service."""

    def __init__(self, service: GenerativeService | None = None) -> None:
        self.service = service or get_generative_service()
        self.provider_name = self.service.provider_name

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
    # The explicit argument is ignored; selection follows configured keys
    # (OpenRouter first, then Gemini, then fallback text).
    _ = provider
    return GenerativeLLMProvider()


# Backwards-compatible alias for the previous class name.
GeminiLLMProvider = GenerativeLLMProvider
