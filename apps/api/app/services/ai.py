"""AI service layer — Knowledge Platform health and configuration."""

from app.core.config import settings
from app.services.knowledge.llm.providers import get_llm_provider


class AIService:
    """AI Knowledge Platform configuration and health."""

    def __init__(self) -> None:
        self.openai_api_key = settings.openai_api_key
        self.gemini_api_key = settings.gemini_api_key
        self.qdrant_host = settings.qdrant_host
        self.qdrant_port = settings.qdrant_port
        self.llm_provider = settings.llm_provider

    @property
    def is_configured(self) -> bool:
        provider = get_llm_provider()
        return provider.provider_name != "fallback"

    async def health_check(self) -> dict:
        provider = get_llm_provider()
        return {
            "ai_configured": self.is_configured,
            "active_provider": provider.provider_name,
            "openai_configured": bool(self.openai_api_key),
            "gemini_configured": bool(self.gemini_api_key),
            "local_llm_configured": bool(settings.local_llm_url),
            "qdrant_host": self.qdrant_host,
            "llm_model": settings.llm_model,
        }
