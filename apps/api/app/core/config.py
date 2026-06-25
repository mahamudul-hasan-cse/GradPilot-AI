from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="GradPilot AI", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")

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

    jwt_secret_key: str = Field(
        default="dev-secret-change-in-production",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_collection: str = Field(default="gradpilot_embeddings", alias="QDRANT_COLLECTION")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")

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

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
    local_llm_url: str | None = Field(default=None, alias="LOCAL_LLM_URL")
    local_llm_model: str = Field(default="llama3", alias="LOCAL_LLM_MODEL")
    knowledge_memory_ttl_seconds: int = Field(default=86400, alias="KNOWLEDGE_MEMORY_TTL_SECONDS")

    document_upload_dir: str = Field(default="uploads", alias="DOCUMENT_UPLOAD_DIR")
    document_ocr_provider: str = Field(default="fallback", alias="DOCUMENT_OCR_PROVIDER")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | List[str]) -> str:
        if isinstance(value, list):
            return ",".join(value)
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def async_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        if self.database_url_sync:
            return self.database_url_sync
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
