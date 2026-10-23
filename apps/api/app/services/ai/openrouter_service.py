"""OpenRouter integration (OpenAI-compatible chat completions)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import present_secret, settings
from app.services.ai.gemini_service import fallback_response

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Retry policy for transient OpenRouter failures (rate limits / 5xx).
_MAX_ATTEMPTS = 3
_BACKOFF_BASE_SECONDS = 1.5
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class OpenRouterService:
    """Thin OpenRouter API client with the same public API as GeminiService."""

    provider_name = "openrouter"

    def __init__(self) -> None:
        self.api_key = present_secret(settings.openrouter_api_key)
        self.model = (settings.openrouter_model or "").strip() or "openai/gpt-4o-mini"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        return await self._complete(
            [{"role": "user", "content": prompt}],
            system=system,
            temperature=temperature,
            fallback_prompt=prompt,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        fallback_prompt = "\n".join(f"{message['role']}: {message['content']}" for message in messages)
        return await self._complete(
            [{"role": message["role"], "content": message["content"]} for message in messages],
            system=system,
            temperature=temperature,
            fallback_prompt=fallback_prompt,
        )

    async def rewrite(self, text: str, instruction: str, *, temperature: float = 0.3) -> str:
        return await self.generate_text(
            f"Rewrite the following text using this instruction:\n{instruction}\n\nText:\n{text}",
            temperature=temperature,
        )

    async def summarize(self, text: str, *, temperature: float = 0.2) -> str:
        return await self.generate_text(f"Summarize this clearly and concisely:\n\n{text}", temperature=temperature)

    async def analyze(self, text: str, *, system: str | None = None, temperature: float = 0.2) -> str:
        return await self.generate_text(
            f"Analyze the following and return practical guidance:\n\n{text}",
            system=system,
            temperature=temperature,
        )

    async def stream_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> AsyncIterator[str]:
        # Mirror GeminiService: chunk the generated text to keep API streaming stable.
        text = await self.generate_text(prompt, system=system, temperature=temperature)
        for word in text.split(" "):
            yield word + " "

    async def _complete(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None,
        temperature: float,
        fallback_prompt: str,
    ) -> str:
        if not self.api_key:
            return fallback_response(fallback_prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://gradpilot.ai",
            "X-Title": "GradPilot AI",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": ([{"role": "system", "content": system}] if system else []) + messages,
            "temperature": temperature,
        }

        last_status: int | None = None
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(1, _MAX_ATTEMPTS + 1):
                try:
                    response = await client.post(_OPENROUTER_URL, json=payload, headers=headers)
                    response.raise_for_status()
                    content = _message_text(response.json())
                    if not content.strip():
                        raise ValueError("empty completion")
                    return content
                except httpx.HTTPStatusError as exc:
                    last_status = exc.response.status_code
                    # Retry transient errors (rate limit / server side); fail fast otherwise.
                    if last_status in _RETRYABLE_STATUS and attempt < _MAX_ATTEMPTS:
                        await asyncio.sleep(_BACKOFF_BASE_SECONDS * attempt)
                        continue
                    logger.warning("OpenRouter request failed (status %s); using fallback.", last_status)
                    break
                except httpx.TransportError as exc:
                    if attempt < _MAX_ATTEMPTS:
                        logger.warning("OpenRouter transport error (%s); retrying.", type(exc).__name__)
                        await asyncio.sleep(_BACKOFF_BASE_SECONDS * attempt)
                        continue
                    logger.warning("OpenRouter transport error (%s); using fallback.", type(exc).__name__)
                    break
                except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                    logger.warning("OpenRouter request error (%s); using fallback.", type(exc).__name__)
                    break

        return fallback_response(fallback_prompt)


def _message_text(data: Any) -> str:
    """Normalize an OpenAI-compatible message content value to text."""

    content = data["choices"][0]["message"]["content"]
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
        return "".join(parts)
    return ""
