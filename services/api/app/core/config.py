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
    # Default from origin/rotation; override via GEMINI_MODEL in .env as needed.
    gemini_model: str = "gemini-3.5-flash-lite"
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
        single-key or comma-separated config), then gemini_api_keys
        (comma-separated rotation pool, docs/work.md B2)."""
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

    # Vector DB Provider (Qdrant Cloud)
    # Default fake so CI/local smoke never require Qdrant Cloud; set
    # VECTOR_DB_PROVIDER=qdrant + QDRANT_URL to enable live vector search.
    vector_db_provider: Literal["fake", "qdrant"] = "fake"
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection_prefix: str = "trellis"

    # Embedding provider for Qdrant / partner match. Defaults to fake
    # (deterministic hash vectors). Set EMBEDDING_PROVIDER=gemini with a
    # Gemini key for real gemini-embedding-001 vectors (3072-dim).
    embedding_provider: Literal["fake", "gemini"] = "fake"
    embedding_model: str = "gemini-embedding-001"
    embedding_dims: int = 32

    # Graph DB Provider (Neo4j). Defaults to fake in-memory provider so
    # CI never requires a live Neo4j instance. Set GRAPH_DB_PROVIDER=neo4j
    # + NEO4J_URI to enable live Graph RAG.
    graph_db_provider: Literal["fake", "neo4j"] = "fake"
    neo4j_uri: str | None = None
    neo4j_user: str = "neo4j"
    neo4j_password: str | None = None

    # YouTube Data API (work.md C2). Comma-separated keys rotate on 403/429.
    youtube_api_key: str | None = None
    # Optional extra pool (same semantics as GEMINI_API_KEYS).
    youtube_api_keys: str = ""
    youtube_timeout_seconds: float = 2.0

    def youtube_api_key_pool(self) -> list[str]:
        """Ordered, de-duplicated YouTube key pool for quota rotation."""
        pool: list[str] = []
        if self.youtube_api_key:
            for raw in self.youtube_api_key.split(","):
                key = raw.strip()
                if key and key not in pool:
                    pool.append(key)
        for raw in self.youtube_api_keys.split(","):
            key = raw.strip()
            if key and key not in pool:
                pool.append(key)
        return pool

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

    # Notion OAuth settings
    notion_oauth_client_id: str | None = None
    notion_oauth_client_secret: str | None = None
    notion_oauth_redirect_uri: str = "http://localhost:8002/api/v1/integrations/notion/callback"

    # Neo4j Graph Provider DI settings
    graph_provider: Literal["fake", "neo4j"] = "fake"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "trellis_password"




def get_settings() -> Settings:
    return Settings()
