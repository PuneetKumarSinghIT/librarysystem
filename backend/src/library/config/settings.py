"""Typed application configuration, loaded from environment / .env (12-factor)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration. Values come from env vars or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── App ──
    env: str = "development"
    log_level: str = "INFO"

    # ── Database ──
    database_url: str = (
        "postgresql+asyncpg://library_app:library_dev_pw@localhost:5432/library"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # ── Auth / JWT ──
    jwt_secret: str = "dev_only_change_me"
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 1_209_600
    argon2_time_cost: int = 3

    # ── Servers ──
    grpc_port: int = 50051
    rest_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # ── Rate limiting ──
    rate_limit_login_per_minute: int = 5

    # ── Lending policy ──
    loan_period_days: int = 14
    fine_per_day: float = 0.25

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
