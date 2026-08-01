"""App configuration. Owner: Backend."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "local"
    auth_bypass: bool = False
    demo_user_id: str = "demo-user-aarav"

    database_url: str = "postgresql+psycopg://trellis:trellis@localhost:5432/trellis"
    redis_url: str | None = "redis://localhost:6379/0"

    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None


def get_settings() -> Settings:
    return Settings()
