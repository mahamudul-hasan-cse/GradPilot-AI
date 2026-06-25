"""LLM provider abstraction — OpenAI, Gemini, and future local models."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


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


class FallbackLLMProvider(LLMProvider):
    """Synthesizes answers from context when no API key is configured."""

    provider_name = "fallback"

    async def generate(self, *, system: str, user: str, temperature: float = 0.2) -> str:
        context_start = user.find("Context:")
        question_start = user.find("Question:")
        context = user[context_start:question_start].strip() if context_start >= 0 and question_start >= 0 else user
        question = user[question_start:].replace("Question:", "").strip() if question_start >= 0 else user
        if not context or "No relevant context" in context:
            return (
                "I don't have enough verified knowledge to answer that question confidently. "
                "Please try rephrasing or ask about universities, scholarships, visas, or admissions."
            )
        excerpt = context[:1200]
        return (
            f"Based on GradPilot's knowledge base:\n\n{excerpt}\n\n"
            f"Regarding your question ({question[:200]}): "
            "the retrieved sources above contain relevant information. "
            "Configure OPENAI_API_KEY or GEMINI_API_KEY for full generative answers with citations."
        )

    async def stream(self, *, system: str, user: str, temperature: float = 0.2) -> AsyncIterator[str]:
        text = await self.generate(system=system, user=user, temperature=temperature)
        for word in text.split(" "):
            yield word + " "


class OpenAILLMProvider(LLMProvider):
    provider_name = "openai"

    def __init__(self) -> None:
        self.api_key = settings.openai_api_key
        self.model = settings.llm_model

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate(self, *, system: str, user: str, temperature: float = 0.2) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def stream(self, *, system: str, user: str, temperature: float = 0.2) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        break
                    try:
                        delta = json.loads(payload)["choices"][0]["delta"].get("content")
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


class GeminiLLMProvider(LLMProvider):
    provider_name = "gemini"

    def __init__(self) -> None:
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate(self, *, system: str, user: str, temperature: float = 0.2) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}"
            f":generateContent?key={self.api_key}"
        )
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url,
                json={
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {"temperature": temperature},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def stream(self, *, system: str, user: str, temperature: float = 0.2) -> AsyncIterator[str]:
        text = await self.generate(system=system, user=user, temperature=temperature)
        for word in text.split(" "):
            yield word + " "


class LocalLLMProvider(LLMProvider):
    """Stub for future on-premise / Ollama integration."""

    provider_name = "local"

    def __init__(self) -> None:
        self.base_url = settings.local_llm_url

    @property
    def is_available(self) -> bool:
        return bool(settings.local_llm_url)

    async def generate(self, *, system: str, user: str, temperature: float = 0.2) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url.rstrip('/')}/v1/chat/completions",
                json={
                    "model": settings.local_llm_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def stream(self, *, system: str, user: str, temperature: float = 0.2) -> AsyncIterator[str]:
        text = await self.generate(system=system, user=user, temperature=temperature)
        for word in text.split(" "):
            yield word + " "


def get_llm_provider(provider: str | None = None) -> LLMProvider:
    chosen = (provider or settings.llm_provider).lower()
    registry: dict[str, LLMProvider] = {
        "openai": OpenAILLMProvider(),
        "gemini": GeminiLLMProvider(),
        "local": LocalLLMProvider(),
        "fallback": FallbackLLMProvider(),
    }
    if chosen in registry and registry[chosen].is_available:
        return registry[chosen]
    for name in (settings.llm_provider, "openai", "gemini", "local"):
        candidate = registry.get(name.lower())
        if candidate and candidate.is_available:
            return candidate
    return registry["fallback"]
