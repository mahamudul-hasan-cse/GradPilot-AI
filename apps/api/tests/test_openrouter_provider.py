"""OpenRouter preference, Gemini fallback, and production env validation."""

from __future__ import annotations

import httpx
import pytest

from app.core.config import Settings, present_secret, settings
from app.core.env_validation import validate_environment
from app.services.ai import AIService, GeminiService, OpenRouterService, get_generative_service
from app.services.knowledge.llm.providers import get_llm_provider

_SECURE_SECRET = "production-secret-value-at-least-32-characters"


def _production(monkeypatch: pytest.MonkeyPatch, *, openrouter: str | None, gemini: str | None) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "jwt_secret_key", _SECURE_SECRET)
    monkeypatch.setattr(settings, "secret_key", _SECURE_SECRET)
    monkeypatch.setattr(settings, "openrouter_api_key", openrouter)
    monkeypatch.setattr(settings, "gemini_api_key", gemini)


class _Response:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://example.test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self) -> dict:
        return self._payload


class _Client:
    posts: list[dict] = []
    scripted: list[_Response] = []

    def __init__(self, *args, **kwargs) -> None:
        self.timeout = kwargs.get("timeout")

    async def __aenter__(self) -> _Client:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def post(self, url, json=None, headers=None):
        _Client.posts.append({"url": url, "json": json, "headers": headers})
        if _Client.scripted:
            item = _Client.scripted.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        return _Response({"choices": [{"message": {"content": "ok"}}]})


@pytest.fixture(autouse=True)
def _reset_http(monkeypatch: pytest.MonkeyPatch):
    _Client.posts = []
    _Client.scripted = []
    monkeypatch.setattr("app.services.ai.openrouter_service.httpx.AsyncClient", _Client)
    monkeypatch.setattr("app.services.ai.gemini_service.httpx.AsyncClient", _Client)
    yield


def test_present_secret_treats_blank_as_unset():
    assert present_secret(None) is None
    assert present_secret("   ") is None
    assert present_secret("  sk-test  ") == "sk-test"


def test_settings_openrouter_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    cfg = Settings(_env_file=None)
    assert cfg.openrouter_api_key is None
    assert cfg.openrouter_model == "openai/gpt-4o-mini"


def test_settings_reads_openrouter_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    cfg = Settings(_env_file=None)
    assert cfg.openrouter_api_key == "test-openrouter-key"
    assert cfg.openrouter_model == "openai/gpt-4o-mini"


def test_production_accepts_openrouter_only(monkeypatch: pytest.MonkeyPatch):
    _production(monkeypatch, openrouter="test-openrouter-key", gemini=None)
    validate_environment()


def test_production_accepts_gemini_only(monkeypatch: pytest.MonkeyPatch):
    _production(monkeypatch, openrouter=None, gemini="test-gemini-key")
    validate_environment()


def test_production_rejects_missing_provider(monkeypatch: pytest.MonkeyPatch):
    _production(monkeypatch, openrouter=None, gemini=None)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY or GEMINI_API_KEY is required in production"):
        validate_environment()


def test_production_rejects_blank_provider_keys(monkeypatch: pytest.MonkeyPatch):
    _production(monkeypatch, openrouter="  ", gemini="  ")
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY or GEMINI_API_KEY is required in production"):
        validate_environment()


def test_openrouter_preferred_when_both_keys_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-openrouter-key")
    monkeypatch.setattr(settings, "openrouter_model", "openai/gpt-4o-mini")
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")
    service = get_generative_service()
    assert isinstance(service, OpenRouterService)
    assert service.provider_name == "openrouter"
    assert get_llm_provider("gemini").provider_name == "openrouter"


def test_gemini_used_when_only_gemini_key_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")
    monkeypatch.setattr(settings, "gemini_model", "gemini-2.5-flash")
    service = get_generative_service()
    assert isinstance(service, GeminiService)
    assert service.provider_name == "gemini"
    assert service.is_available is True
    assert get_llm_provider().provider_name == "gemini"


def test_blank_openrouter_key_falls_through_to_gemini(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "   ")
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")
    service = get_generative_service()
    assert isinstance(service, GeminiService)
    assert service.is_available is True


@pytest.mark.asyncio
async def test_openrouter_chat_completion_request(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "  test-openrouter-key  ")
    monkeypatch.setattr(settings, "openrouter_model", "openai/gpt-4o-mini")
    monkeypatch.setattr(settings, "gemini_api_key", None)
    _Client.scripted = [_Response({"choices": [{"message": {"content": "Study in Canada."}}]})]

    service = get_generative_service()
    text = await service.generate_text("Hello", system="Be brief", temperature=0.1)

    assert text == "Study in Canada."
    assert len(_Client.posts) == 1
    call = _Client.posts[0]
    assert call["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer test-openrouter-key"
    assert "test-openrouter-key" not in call["url"]
    assert call["json"]["model"] == "openai/gpt-4o-mini"
    assert call["json"]["temperature"] == 0.1
    assert call["json"]["messages"] == [
        {"role": "system", "content": "Be brief"},
        {"role": "user", "content": "Hello"},
    ]


@pytest.mark.asyncio
async def test_openrouter_normalizes_list_content(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-openrouter-key")
    monkeypatch.setattr(settings, "openrouter_model", "openai/gpt-4o-mini")
    monkeypatch.setattr(settings, "gemini_api_key", None)
    _Client.scripted = [
        _Response({"choices": [{"message": {"content": [{"type": "text", "text": "Part A"}, " and B"]}}]})
    ]

    text = await get_generative_service().chat([{"role": "user", "content": "Hi"}])
    assert text == "Part A and B"


@pytest.mark.asyncio
async def test_openrouter_retries_rate_limit_then_succeeds(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-openrouter-key")
    monkeypatch.setattr(settings, "gemini_api_key", None)

    async def _no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("app.services.ai.openrouter_service.asyncio.sleep", _no_sleep)
    _Client.scripted = [
        _Response({}, status_code=429),
        _Response({"choices": [{"message": {"content": "retried"}}]}),
    ]

    text = await OpenRouterService().generate_text("Hello")
    assert text == "retried"
    assert len(_Client.posts) == 2


@pytest.mark.asyncio
async def test_openrouter_retries_transport_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-openrouter-key")
    monkeypatch.setattr(settings, "gemini_api_key", None)

    async def _no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("app.services.ai.openrouter_service.asyncio.sleep", _no_sleep)
    _Client.scripted = [
        httpx.ConnectError("temporary"),
        _Response({"choices": [{"message": {"content": "after reconnect"}}]}),
    ]

    text = await OpenRouterService().generate_text("Hello")
    assert text == "after reconnect"
    assert len(_Client.posts) == 2


@pytest.mark.asyncio
async def test_gemini_request_when_only_gemini_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")
    monkeypatch.setattr(settings, "gemini_model", "gemini-2.5-flash")
    _Client.scripted = [
        _Response({"candidates": [{"content": {"parts": [{"text": "Gemini answer"}]}}]})
    ]

    provider = get_llm_provider("openrouter")
    text = await provider.generate(system="Be brief", user="Hello", temperature=0.2)

    assert text == "Gemini answer"
    assert provider.provider_name == "gemini"
    assert len(_Client.posts) == 1
    call = _Client.posts[0]
    assert call["url"] == (
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    )
    assert "key=" not in call["url"]
    assert call["headers"]["x-goog-api-key"] == "test-gemini-key"
    assert call["json"]["systemInstruction"] == {"parts": [{"text": "Be brief"}]}
    assert call["json"]["contents"][0]["parts"][0]["text"] == "Hello"


@pytest.mark.asyncio
async def test_health_reports_active_provider(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-openrouter-key")
    monkeypatch.setattr(settings, "openrouter_model", "openai/gpt-4o-mini")
    monkeypatch.setattr(settings, "gemini_api_key", None)

    health = await AIService().health_check()
    assert health["ai_configured"] is True
    assert health["active_provider"] == "openrouter"
    assert health["openrouter_configured"] is True
    assert health["gemini_configured"] is False
    assert health["llm_model"] == "openai/gpt-4o-mini"

    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")
    monkeypatch.setattr(settings, "gemini_model", "gemini-2.5-flash")
    health = await AIService().health_check()
    assert health["active_provider"] == "gemini"
    assert health["gemini_configured"] is True
    assert health["llm_model"] == "gemini-2.5-flash"

    monkeypatch.setattr(settings, "gemini_api_key", None)
    health = await AIService().health_check()
    assert health["ai_configured"] is False
    assert health["active_provider"] == "fallback"
    assert health["llm_model"] is None


@pytest.mark.asyncio
async def test_fallback_mentions_either_provider(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", None)
    text = await get_generative_service().generate_text("Context:\nVisa guide\nQuestion:\nWhat visa?")
    assert "OPENROUTER_API_KEY or GEMINI_API_KEY" in text
