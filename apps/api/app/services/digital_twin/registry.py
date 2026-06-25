"""Service registry for intelligence modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Coroutine


@dataclass
class RegisteredService:
    name: str
    description: str
    version: str
    capabilities: list[str]
    handler: Callable[..., Coroutine[Any, Any, Any]] | None = None


class ServiceRegistry:
    """Central registry of all GradPilot intelligence modules."""

    _services: dict[str, RegisteredService] = {}

    @classmethod
    def register(
        cls,
        name: str,
        *,
        description: str,
        version: str = "1.0.0",
        capabilities: list[str] | None = None,
        handler: Callable[..., Coroutine[Any, Any, Any]] | None = None,
    ) -> None:
        cls._services[name] = RegisteredService(
            name=name,
            description=description,
            version=version,
            capabilities=capabilities or [],
            handler=handler,
        )

    @classmethod
    def get(cls, name: str) -> RegisteredService | None:
        return cls._services.get(name)

    @classmethod
    def list_services(cls) -> list[RegisteredService]:
        return list(cls._services.values())

    @classmethod
    def clear(cls) -> None:
        cls._services.clear()


def bootstrap_registry() -> None:
    """Register all platform intelligence modules."""
    if ServiceRegistry.get("profile_intelligence"):
        return

    ServiceRegistry.register(
        "profile_intelligence",
        description="Admission readiness, strengths, weaknesses, and improvement recommendations",
        capabilities=["analyze", "score", "recommend_actions"],
    )
    ServiceRegistry.register(
        "university_recommendation",
        description="Safe / Target / Ambitious university matching",
        capabilities=["recommend", "score", "explain"],
    )
    ServiceRegistry.register(
        "scholarship_matching",
        description="Scholarship eligibility scoring and ranking",
        capabilities=["match", "score", "explain"],
    )
    ServiceRegistry.register(
        "knowledge_platform",
        description="RAG knowledge Q&A with citations",
        capabilities=["search", "chat", "cite"],
    )
    ServiceRegistry.register(
        "application_workspace",
        description="Application progress, tasks, deadlines, and timeline",
        capabilities=["track", "tasks", "deadlines", "progress"],
    )
    ServiceRegistry.register(
        "document_intelligence",
        description="OCR, classification, extraction, validation, and twin sync for admission documents",
        version="1.0.0",
        capabilities=["upload", "ocr", "classify", "extract", "validate", "version", "twin_sync"],
    )
    ServiceRegistry.register(
        "digital_twin",
        description="Unified student state and AI orchestration",
        capabilities=["aggregate", "orchestrate", "refresh", "timeline"],
    )
