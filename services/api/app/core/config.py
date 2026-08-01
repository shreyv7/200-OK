"""App configuration. Owner: Backend."""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "local"
    auth_bypass: bool = False
    # Only used when ENV=local AND AUTH_BYPASS=true (pytest / local smoke).
    # Never referenced by seed/prewarm unless ALLOW_DEMO_SEED / PREWARM_USER_ID set.
    demo_user_id: str = "demo-user-aarav"
    # Explicit opt-in for the Aarav seed script (A2/A5 — no silent prod seeding).
    allow_demo_seed: bool = False

    database_url: str = "postgresql+psycopg://trellis:trellis@localhost:5432/trellis"
    redis_url: str | None = "redis://localhost:6379/0"

    clerk_secret_key: str | None = None
    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None
    # Optional JWT `aud` (set when your Clerk session template includes audience).
    clerk_audience: str | None = None
    # Comma-separated frontend origins / app IDs allowed in JWT `azp` claim.
    clerk_authorized_parties: str = (
        "http://localhost:8080,http://127.0.0.1:8080,"
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    # Optional: prewarm a specific user stack (never defaults to demo_user_id).
    prewarm_user_id: str | None = None

    @property
    def clerk_authorized_party_list(self) -> list[str]:
        return [p.strip() for p in self.clerk_authorized_parties.split(",") if p.strip()]

    # LLM provider DI (milestones.md M3). Defaults to the deterministic fake
    # so tests/local dev never require live Gemini credentials.
    llm_provider: Literal["fake", "gemini", "bedrock"] = "fake"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    bedrock_region: str | None = None
    bedrock_model_id: str | None = None

    # SearchProvider DI (milestones.md M4). Defaults to the deterministic
    # fake so tests/local dev never require a live Tavily key.
    search_provider: Literal["fake", "tavily"] = "fake"
    tavily_api_key: str | None = None
    tavily_timeout_seconds: float = 1.5


def get_settings() -> Settings:
    return Settings()
