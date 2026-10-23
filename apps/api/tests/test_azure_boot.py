"""Boot rules for the Azure Container Apps image."""

from pathlib import Path

from app.core.config import normalize_async_database_url, settings_dirs


def test_azure_postgres_url_uses_asyncpg_ssl():
    url = normalize_async_database_url(
        "postgresql://gradpilot:p%40ss@psql.postgres.database.azure.com:5432/gradpilot?sslmode=require"
    )

    assert url.startswith("postgresql+asyncpg://")
    assert "sslmode=" not in url
    assert "ssl=require" in url
    assert "p%40ss" in url


def test_existing_asyncpg_url_is_preserved():
    url = normalize_async_database_url("postgresql+asyncpg://gradpilot:secret@localhost:5432/gradpilot")

    assert url == "postgresql+asyncpg://gradpilot:secret@localhost:5432/gradpilot"


def test_asyncpg_sslmode_is_rewritten_without_changing_scheme():
    url = normalize_async_database_url(
        "postgresql+asyncpg://gradpilot:secret@localhost:5432/gradpilot?sslmode=require"
    )

    assert url.startswith("postgresql+asyncpg://")
    assert "sslmode=" not in url
    assert url.endswith("ssl=require")


def test_container_layout_does_not_require_a_monorepo_root():
    root, api_dir = settings_dirs(Path("/app/app/core/config.py"))

    assert api_dir == Path("/app")
    assert root == Path("/app")


def test_repo_layout_still_finds_the_workspace_root():
    root, api_dir = settings_dirs(Path("/workspace/apps/api/app/core/config.py"))

    assert api_dir == Path("/workspace/apps/api")
    assert root == Path("/workspace")
