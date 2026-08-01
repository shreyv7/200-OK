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
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000"
    )
    # Optional: prewarm a specific user stack (never defaults to demo_user_id).
    prewarm_user_id: str | None = None

    # A6 — comma-separated browser origins allowed by CORS (never "*"+credentials in prod).
    cors_origins: str = (
        "http://localhost:8080,http://127.0.0.1:8080,"
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000"
    )

    @property
    def clerk_authorized_party_list(self) -> list[str]:
        return [p.strip() for p in self.clerk_authorized_parties.split(",") if p.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # LLM provider DI (milestones.md M3). Defaults to the deterministic fake
    # so tests/local dev never require live Gemini credentials.
    llm_provider: Literal["fake", "gemini", "bedrock"] = "fake"
    gemini_api_key: str | None = None
    # Additional keys for round-robin rotation (docs/work.md B2), comma-
    # separated. Combined with gemini_api_key (kept for back-compat single-
    # key config) via gemini_api_key_pool() below.
    gemini_api_keys: str = ""
    # gemini-1.5-flash 404s against the current v1beta API (retired) —
    # verified live while wiring B1 (docs/work.md).
    gemini_model: str = "gemini-2.0-flash"
    bedrock_region: str | None = None
    bedrock_model_id: str | None = None
    # Off by default (docs/work.md B3 ground rule: "if we don't buy
    # Bedrock yet, ship the failover code behind a flag"). When true AND
    # bedrock_region/bedrock_model_id are both set, LLM_PROVIDER=gemini
    # wraps the Gemini pool in FailoverLLMProvider so a fully-exhausted
    # Gemini pool automatically retries on Bedrock instead of failing.
    bedrock_failover_enabled: bool = False
    # Per-user daily LLM call cap (docs/work.md B5). Applies regardless of
    # which underlying provider actually serves a call (Gemini or, if
    # failover is on, Bedrock) — see app/providers/llm/budget.py.
    llm_daily_call_cap: int = 200

    def gemini_api_key_pool(self) -> list[str]:
        """Ordered, de-duplicated key pool: gemini_api_key first (back-compat
        single-key config), then gemini_api_keys (comma-separated rotation
        pool, docs/work.md B2)."""
        pool: list[str] = []
        if self.gemini_api_key:
            pool.append(self.gemini_api_key)
        for raw in self.gemini_api_keys.split(","):
            key = raw.strip()
            if key and key not in pool:
                pool.append(key)
        return pool

    # SearchProvider DI (milestones.md M4). Defaults to the deterministic
    # fake so tests/local dev never require a live Tavily key.
    search_provider: Literal["fake", "tavily"] = "fake"
    tavily_api_key: str | None = None
    tavily_timeout_seconds: float = 1.5

    # YouTube Data API (work.md C2).
    youtube_api_key: str | None = None
    youtube_timeout_seconds: float = 2.0

    # Token encryption key for OAuth credentials (Fernet symmetric key)
    token_encryption_key: str | None = None

    # Google OAuth settings
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    google_oauth_redirect_uri: str = "http://localhost:8002/api/v1/integrations/google-calendar/callback"

    # GitHub OAuth settings
    github_oauth_client_id: str | None = None
    github_oauth_client_secret: str | None = None
    github_oauth_redirect_uri: str = "http://localhost:8002/api/v1/integrations/github/callback"




def get_settings() -> Settings:
    return Settings()
