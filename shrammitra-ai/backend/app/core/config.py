"""
Application configuration management.

Uses pydantic-settings for type-safe, validated settings loaded from
environment variables and/or .env file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings validated at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "ShramMitra AI"
    APP_ENV: str = Field(default="development", pattern="^(development|staging|production)$")
    APP_DEBUG: bool = False
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    SECRET_KEY: str = Field(min_length=32)
    ADMIN_API_KEY: str = Field(min_length=16)
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    SESSION_TTL_SECONDS: int = 3600

    # ── AWS ───────────────────────────────────────────────────────────────────
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_MAX_TOKENS: int = 2048
    BEDROCK_TEMPERATURE: float = 0.1

    S3_BUCKET_DOCUMENTS: str = "shrammitra-documents"
    S3_BUCKET_AUDIO: str = "shrammitra-audio"

    TRANSCRIBE_REGION: str = "ap-south-1"
    POLLY_REGION: str = "ap-south-1"

    USE_SECRETS_MANAGER: bool = False
    SECRETS_MANAGER_PREFIX: str = "shrammitra/prod/"

    # ── Elasticsearch ─────────────────────────────────────────────────────────
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_API_KEY: str = ""
    ELASTICSEARCH_INDEX_NAME: str = "shrammitra_labour_docs_v1"
    ELASTICSEARCH_INDEX_ALIAS: str = "shrammitra_labour_docs"

    JINA_EMBEDDING_MODEL: str = "jina-embeddings-v3"
    EMBEDDING_DIMENSION: int = 1024

    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    RAG_MAX_CONTEXT_TOKENS: int = 3000

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_API_VERSION: str = "v19.0"
    WHATSAPP_API_BASE_URL: str = "https://graph.facebook.com"
    WHATSAPP_APP_SECRET: str = ""

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_BURST: int = 10
    GLOBAL_RATE_LIMIT_PER_MINUTE: int = 1000

    # ── Voice / S3 (optional — disable if S3 is not available) ─────────────
    ENABLE_VOICE: bool = True  # Set to false if S3 is blocked (e.g., AWS Workshop accounts)

    # ── Monitoring ────────────────────────────────────────────────────────────
    CLOUDWATCH_NAMESPACE: str = "ShramMitra/Application"
    ENABLE_METRICS: bool = True
    SENTRY_DSN: str = ""

    # ── Supported Languages ───────────────────────────────────────────────────
    SUPPORTED_LANGUAGES: List[str] = ["en", "hi", "kn", "ta", "te", "bn", "or"]
    DEFAULT_LANGUAGE: str = "en"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list) -> list:
        """Parse comma-separated CORS origins string into list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: str | list) -> list:
        """Parse comma-separated allowed hosts string into list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v

    @property
    def whatsapp_api_url(self) -> str:
        """Construct WhatsApp API base URL."""
        return f"{self.WHATSAPP_API_BASE_URL}/{self.WHATSAPP_API_VERSION}"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
