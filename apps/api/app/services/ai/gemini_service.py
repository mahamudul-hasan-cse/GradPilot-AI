"""Single Gemini integration for all generative AI operations."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import present_secret, settings

logger = logging.getLogger(__name__)

# Retry policy for transient Gemini failures (rate limits / 5xx).
_MAX_ATTEMPTS = 3
_BACKOFF_BASE_SECONDS = 1.5


class GeminiService:
    """Thin Gemini API client used by advisor, SOP, and future AI features."""

    provider_name = "gemini"

    def __init__(self) -> None:
        self.api_key = present_secret(settings.gemini_api_key)
        self.model = settings.gemini_model

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
        if not self.api_key:
            return fallback_response(prompt)

        # The key is passed via header so it never appears in URLs or logs.
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}"
            f":generateContent"
        )
        headers = {"x-goog-api-key": self.api_key}
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        last_status: int | None = None
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(1, _MAX_ATTEMPTS + 1):
                try:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except httpx.HTTPStatusError as exc:
                    last_status = exc.response.status_code
                    # Retry transient errors (rate limit / server side); fail fast otherwise.
                    if last_status in (429, 500, 502, 503, 504) and attempt < _MAX_ATTEMPTS:
                        await asyncio.sleep(_BACKOFF_BASE_SECONDS * attempt)
                        continue
                    logger.warning("Gemini request failed (status %s); using fallback.", last_status)
                    break
                except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
                    logger.warning("Gemini request error (%s); using fallback.", type(exc).__name__)
                    break

        return fallback_response(prompt)

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        prompt = "\n".join(f"{message['role']}: {message['content']}" for message in messages)
        return await self.generate_text(prompt, system=system, temperature=temperature)

    async def rewrite(self, text: str, instruction: str, *, temperature: float = 0.3) -> str:
        return await self.generate_text(
            f"Rewrite the following text using this instruction:\n{instruction}\n\nText:\n{text}",
            temperature=temperature,
        )

    async def summarize(self, text: str, *, temperature: float = 0.2) -> str:
        return await self.generate_text(f"Summarize this clearly and concisely:\n\n{text}", temperature=temperature)

    async def analyze(self, text: str, *, system: str | None = None, temperature: float = 0.2) -> str:
        return await self.generate_text(f"Analyze the following and return practical guidance:\n\n{text}", system=system, temperature=temperature)

    async def stream_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> AsyncIterator[str]:
        # Gemini streaming can be added later; keep API streaming stable by chunking the generated text.
        text = await self.generate_text(prompt, system=system, temperature=temperature)
        for word in text.split(" "):
            yield word + " "


def fallback_response(prompt: str) -> str:
    context_start = prompt.find("Context:")
    question_start = prompt.find("Question:")
    context = prompt[context_start:question_start].strip() if context_start >= 0 and question_start >= 0 else prompt
    question = prompt[question_start:].replace("Question:", "").strip() if question_start >= 0 else prompt
    if not context or "No relevant context" in context:
        return (
            "I don't have enough verified knowledge to answer that confidently yet. "
            "Please add more profile details or ask about universities, scholarships, visas, or admissions."
        )
    return (
        f"Based on GradPilot's available knowledge:\n\n{context[:1200]}\n\n"
        f"Regarding your question ({question[:200]}), the context above contains the most relevant guidance. "
        "Add OPENROUTER_API_KEY or GEMINI_API_KEY for a fuller AI-generated response."
    )
