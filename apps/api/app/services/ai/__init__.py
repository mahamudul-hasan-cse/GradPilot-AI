"""AI service package.

OpenRouter is preferred when OPENROUTER_API_KEY is set; Gemini is used when only
GEMINI_API_KEY is set; otherwise GeminiService serves the built-in fallback text.
"""

from app.core.config import present_secret, settings
from app.services.ai.gemini_service import GeminiService
from app.services.ai.openrouter_service import OpenRouterService

GenerativeService = OpenRouterService | GeminiService


def get_generative_service() -> GenerativeService:
    """Return the preferred configured generative AI service."""

    if present_secret(settings.openrouter_api_key):
        return OpenRouterService()
    # GeminiService also covers the no-key case via its fallback responses.
    return GeminiService()


class AIService:
    """AI configuration and health status."""

    def __init__(self) -> None:
        self.service = get_generative_service()

    @property
    def is_configured(self) -> bool:
        return self.service.is_available

    async def health_check(self) -> dict:
        return {
            "ai_configured": self.is_configured,
            "active_provider": self.service.provider_name if self.is_configured else "fallback",
            "openrouter_configured": present_secret(settings.openrouter_api_key) is not None,
            "gemini_configured": present_secret(settings.gemini_api_key) is not None,
            "qdrant_host": settings.qdrant_host,
            "llm_model": self.service.model if self.is_configured else None,
        }


__all__ = ["AIService", "GeminiService", "OpenRouterService", "get_generative_service"]
