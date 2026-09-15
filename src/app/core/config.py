from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Customer Support AI Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # API
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    DATABASE_URL: str  # required, no default
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_BROKER_URL: str = "redis://localhost:6379/1"
    REDIS_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # JWT
    JWT_SECRET_KEY: str  # required
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_AGENT_TOKEN_EXPIRE_MINUTES: int = 60

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT: int = 60

    # Observability — OpenTelemetry / Jaeger
    OTEL_ENABLED: bool = False
    OTEL_EXPORTER_JAEGER_ENDPOINT: str = "http://localhost:14268/api/traces"
    OTEL_SERVICE_NAME: str = "customer-support-api"

    # Observability — LangFuse (LLM tracing)
    LANGFUSE_ENABLED: bool = False
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://us.cloud.langfuse.com"

    # Policy
    POLICY_CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # Approval
    APPROVAL_SLA_HOURS: int = 4  # business hours

    # Webhooks
    WEBHOOK_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
