"""App configuration. Owner: Backend."""

from __future__ import annotations

from typing import Literal

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

    # LLM provider DI (milestones.md M3). Defaults to the deterministic fake
    # so tests/local dev never require live Gemini credentials.
    llm_provider: Literal["fake", "gemini", "bedrock"] = "fake"
    gemini_api_key: str | None = None
    gemini_api_keys: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    bedrock_region: str | None = None
    bedrock_model_id: str | None = None
    bedrock_failover_enabled: bool = False
    llm_daily_call_cap: int = 200

    def gemini_api_key_pool(self) -> list[str]:
        """Ordered, de-duplicated key pool: gemini_api_key first (back-compat
        single-key or comma-separated config), then gemini_api_keys (comma-separated
        rotation pool, docs/work.md B2)."""
        pool: list[str] = []
        if self.gemini_api_key:
            for raw in self.gemini_api_key.split(","):
                key = raw.strip()
                if key and key not in pool:
                    pool.append(key)
        if self.gemini_api_keys:
            for raw in self.gemini_api_keys.split(","):
                key = raw.strip()
                if key and key not in pool:
                    pool.append(key)
        return pool

    # SearchProvider DI (milestones.md M4). Defaults to the deterministic
    # fake so tests/local dev never require a live Tavily key.
    search_provider: Literal["fake", "tavily", "youtube", "combined"] = "fake"
    tavily_api_key: str | None = None
    tavily_timeout_seconds: float = 1.5


def get_settings() -> Settings:
    return Settings()
