"""Application configuration.

Settings are loaded from environment variables (and a local .env in dev) via
pydantic-settings. Secrets are read here from the environment ONLY; they are
never logged, never written to the database as ordinary data, and never injected
into prompts. Provider credentials are referenced elsewhere by their env-var
*key*, resolved at call time, and discarded.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Auth / crypto
    secret_key: str = Field(default="dev-only-insecure-change-me-please-32chars")
    access_token_ttl_seconds: int = 900
    refresh_token_ttl_seconds: int = 1209600

    # CORS — comma-separated origins; "*" for dev only.
    cors_origins: str = Field(default="*")

    #: The insecure default that must never run in production.
    INSECURE_DEFAULT_SECRET: str = "dev-only-insecure-change-me-please-32chars"  # noqa: S105

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://agenticubed:agenticubed@db:5432/agenticubed"
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg://agenticubed:agenticubed@db:5432/agenticubed"
    )

    # Redis / Celery
    redis_url: str = Field(default="redis://redis:6379/0")
    celery_broker_url: str = Field(default="redis://redis:6379/1")
    celery_result_backend: str = Field(default="redis://redis:6379/2")

    # Artifact store
    artifact_store_backend: str = Field(default="local")
    artifact_store_path: str = Field(default="/var/artifacts")

    # Live event stream — "memory" (single process) or "redis" (multi-process)
    event_bus_backend: str = Field(default="memory")

    # Task dispatch — "inline" executes in the API request (dev/tests);
    # "celery" queues to the worker via the WorkflowEngine port (compose/prod).
    workflow_engine_backend: str = Field(default="inline")

    # Dependency-aware scheduling — max tasks in flight per project.
    scheduler_max_parallel: int = Field(default=3, ge=1)

    # Predecessor-output handoff — total chars of prerequisite output injected
    # into a successor task's prompt (WS-3).
    handoff_budget_chars: int = Field(default=8000, ge=0)

    # Providers
    default_provider: str = Field(default="mock")
    anthropic_api_key: str = Field(default="")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def assert_production_safe(self) -> None:
        """Refuse to run in production with the insecure default secret."""
        if self.is_production and self.secret_key == self.INSECURE_DEFAULT_SECRET:
            raise RuntimeError(
                "SECRET_KEY is the insecure default; set a strong SECRET_KEY in production."
            )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
