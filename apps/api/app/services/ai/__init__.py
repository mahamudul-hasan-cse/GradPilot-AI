"""AI service package.

Gemini is the only generative AI engine for the MVP.
"""

from app.core.config import settings
from app.services.ai.gemini_service import GeminiService


class AIService:
    """AI configuration and health status."""

    def __init__(self) -> None:
        self.gemini = GeminiService()

    @property
    def is_configured(self) -> bool:
        return self.gemini.is_available

    async def health_check(self) -> dict:
        return {
            "ai_configured": self.is_configured,
            "active_provider": "gemini" if self.is_configured else "fallback",
            "gemini_configured": bool(settings.gemini_api_key),
            "qdrant_host": settings.qdrant_host,
            "llm_model": settings.gemini_model,
        }


__all__ = ["AIService", "GeminiService"]
