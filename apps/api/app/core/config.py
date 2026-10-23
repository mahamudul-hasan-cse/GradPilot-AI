from functools import lru_cache
from pathlib import Path
from typing import List, Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG_FILE = Path(__file__).resolve()
# apps/api/app/core/config.py -> API root is parents[2].
# The container image copies that tree to /app, which has no monorepo root above it.
API_DIR = _CONFIG_FILE.parents[2]
ROOT_DIR = _CONFIG_FILE.parents[4] if len(_CONFIG_FILE.parents) > 4 else API_DIR


def settings_dirs(config_file: Path) -> tuple[Path, Path]:
    """Return (repo_or_api_root, api_root) without assuming a monorepo layout."""

    api_dir = config_file.parents[2]
    root_dir = config_file.parents[4] if len(config_file.parents) > 4 else api_dir
    return root_dir, api_dir


def _env_files() -> tuple[str, ...]:
    files: list[Path] = []
    if len(_CONFIG_FILE.parents) > 4:
        files.append(_CONFIG_FILE.parents[4] / ".env")
    files.append(API_DIR / ".env")
    return tuple(str(path) for path in files)


def normalize_async_database_url(url: str) -> str:
    """Return a SQLAlchemy asyncpg URL.

    Azure Flexible Server strings use libpq's ``sslmode=require``.
    asyncpg rejects that parameter and expects ``ssl=require``.
    """

    if url.startswith("postgres://") and not url.startswith("postgresql://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    parts = urlsplit(url)
    needs_ssl = False
    saw_ssl = False
    rewritten: list[tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "ssl":
            saw_ssl = True
            rewritten.append((key, value))
        elif key == "sslmode":
            if value.lower() in {"require", "verify-ca", "verify-full", "prefer"}:
                needs_ssl = True
        elif key == "channel_binding":
            continue
        else:
            rewritten.append((key, value))
    if needs_ssl and not saw_ssl:
        rewritten.append(("ssl", "require"))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(rewritten), parts.fragment))


_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "[::1]", "::1"})


def is_loopback_origin(origin: str) -> bool:
    host = urlsplit(origin).hostname or ""
    return host.lower() in _LOOPBACK_HOSTS or host.lower().endswith(".localhost")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="GradPilot AI", alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"))
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    cors_origins: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    postgres_user: str = Field(default="gradpilot", alias="POSTGRES_USER")
    postgres_password: str = Field(default="gradpilot_secret", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="gradpilot", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    database_url_sync: str | None = Field(default=None, alias="DATABASE_URL_SYNC")

    secret_key: str = Field(
        default="dev-secret-change-in-production",
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET", "JWT_SECRET_KEY"),
    )
    jwt_secret_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("JWT_SECRET", "JWT_SECRET_KEY", "SECRET_KEY"),
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )

    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_collection: str = Field(default="gradpilot_embeddings", alias="QDRANT_COLLECTION")
    embedding_model: str = Field(default="fallback", alias="EMBEDDING_MODEL")

    ingestion_user_agent: str = Field(
        default="GradPilotBot/1.0 (+https://gradpilot.ai/bot)",
        alias="INGESTION_USER_AGENT",
    )
    ingestion_concurrency: int = Field(default=10, alias="INGESTION_CONCURRENCY")
    ingestion_rate_limit_per_domain: float = Field(default=1.0, alias="INGESTION_RATE_LIMIT_PER_DOMAIN")
    ingestion_timeout_seconds: float = Field(default=30.0, alias="INGESTION_TIMEOUT_SECONDS")
    ingestion_batch_size: int = Field(default=50, alias="INGESTION_BATCH_SIZE")
    ingestion_full_batch_size: int = Field(default=200, alias="INGESTION_FULL_BATCH_SIZE")
    ingestion_respect_robots: bool = Field(default=True, alias="INGESTION_RESPECT_ROBOTS")
    ingestion_incremental_cron: str = Field(default="0 */6 * * *", alias="INGESTION_INCREMENTAL_CRON")
    ingestion_full_cron: str = Field(default="0 2 * * 0", alias="INGESTION_FULL_CRON")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_enabled: bool = Field(default=True, alias="REDIS_ENABLED")
    recommendation_cache_ttl_seconds: int = Field(default=3600, alias="RECOMMENDATION_CACHE_TTL_SECONDS")

    llm_model: str = Field(default="gemini-1.5-flash", alias="LLM_MODEL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-4o-mini", alias="OPENROUTER_MODEL")
    knowledge_memory_ttl_seconds: int = Field(default=86400, alias="KNOWLEDGE_MEMORY_TTL_SECONDS")

    document_upload_dir: str = Field(default="uploads", validation_alias=AliasChoices("UPLOAD_DIR", "DOCUMENT_UPLOAD_DIR"))
    document_ocr_provider: str = Field(default="fallback", alias="DOCUMENT_OCR_PROVIDER")
    # "blob" is reserved for Azure Blob storage (not implemented yet; falls back to local).
    upload_backend: Literal["local", "blob"] = Field(default="local", alias="UPLOAD_BACKEND")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | List[str]) -> str:
        if isinstance(value, list):
            return ",".join(value)
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.is_production:
            # Local dev origins must never be trusted by the production API,
            # even if CORS_ORIGINS on the host still lists them.
            origins = [origin for origin in origins if not is_loopback_origin(origin)]
        return origins

    @property
    def async_database_url(self) -> str:
        if self.database_url:
            return normalize_async_database_url(self.database_url)
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        if self.database_url_sync:
            return self.database_url_sync
        if self.database_url:
            if self.database_url.startswith("postgresql+asyncpg://"):
                return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
            if self.database_url.startswith("postgresql://"):
                return self.database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def effective_jwt_secret(self) -> str:
        return self.jwt_secret_key or self.secret_key


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def present_secret(value: str | None) -> str | None:
    """Return a stripped secret, or None when the value is missing or blank."""

    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
