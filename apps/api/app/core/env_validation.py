"""Startup environment validation."""

from __future__ import annotations

from app.core.config import settings

INSECURE_SECRET_VALUES = {
    "dev-secret-change-in-production",
    "change-me",
    "change-me-to-a-long-random-secret-in-production",
}


def validate_environment() -> None:
    """Fail fast only for production-unsafe configuration."""

    if not settings.is_production:
        return

    secret = settings.effective_jwt_secret
    if secret in INSECURE_SECRET_VALUES or len(secret) < 32:
        raise RuntimeError("JWT_SECRET must be set to a secure 32+ character value in production")

    if settings.debug:
        raise RuntimeError("DEBUG must be false in production")

    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is required in production")
