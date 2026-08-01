"""Dependency-injection surface. Owner: Backend.

Central place other modules import `Depends(...)` wiring from, per
techstack.md §5.4 (DB sessions, current user, repositories, providers).
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.security import get_current_user_id
from app.providers.llm.base import LLMProvider
from app.providers.llm.fake import FakeLLMProvider
from app.providers.search.base import SearchProvider
from app.providers.search.fake import FakeSearchProvider


def get_llm_provider(settings: Settings = Depends(get_settings)) -> LLMProvider:
    """Select the configured LLMProvider. Defaults to fake — never requires
    live credentials unless LLM_PROVIDER is explicitly set."""
    if settings.llm_provider == "gemini":
        api_keys = settings.gemini_api_key_pool()
        if not api_keys:
            raise RuntimeError("LLM_PROVIDER=gemini requires GEMINI_API_KEY or GEMINI_API_KEYS to be set")
        from app.providers.llm.gemini import GeminiLLMProvider

        gemini_provider = GeminiLLMProvider(api_keys=api_keys, model=settings.gemini_model)

        if settings.bedrock_failover_enabled and settings.bedrock_region and settings.bedrock_model_id:
            from app.providers.llm.bedrock import BedrockLLMProvider
            from app.providers.llm.failover import FailoverLLMProvider

            bedrock_provider = BedrockLLMProvider(
                region=settings.bedrock_region, model_id=settings.bedrock_model_id
            )
            return FailoverLLMProvider(primary=gemini_provider, fallback=bedrock_provider)

        return gemini_provider

    if settings.llm_provider == "bedrock":
        from app.providers.llm.bedrock import BedrockLLMProvider

        return BedrockLLMProvider(
            region=settings.bedrock_region, model_id=settings.bedrock_model_id
        )

    return FakeLLMProvider()


def wrap_llm_provider_with_budget(
    provider: LLMProvider, db: Session, user_id: str, settings: Settings
) -> LLMProvider:
    """Shared by get_budgeted_llm_provider() and any caller that must
    build its own db Session outside the normal FastAPI request/Depends
    lifecycle — e.g. stack.py's BackgroundTasks refresh, which explicitly
    opens a fresh session because the request-scoped one is already
    closed by the time the task runs. Never call get_budgeted_llm_provider
    from a background task for that reason: it would capture a Session
    that gets torn down before the task's LLM call ever happens.

    The fake provider is never budgeted — it costs nothing, and budgeting
    it would let unrelated tests sharing a user_id interfere with each
    other's call counts for no reason. (docs/work.md B5)"""
    if settings.llm_provider == "fake":
        return provider

    from app.providers.llm.budget import BudgetedLLMProvider

    return BudgetedLLMProvider(
        provider, db=db, user_id=user_id, daily_call_cap=settings.llm_daily_call_cap
    )


def get_budgeted_llm_provider(
    provider: LLMProvider = Depends(get_llm_provider),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> LLMProvider:
    """Wraps get_llm_provider() with a per-user daily call cap
    (docs/work.md B5). Only safe for handlers that use the LLM provider
    synchronously within the request/response cycle — see
    wrap_llm_provider_with_budget()'s docstring for the background-task
    caveat.

    Takes `provider` via Depends(get_llm_provider) rather than calling
    get_llm_provider(settings) directly — FastAPI's app.dependency_overrides
    (used by every test that injects a fake/stub LLM provider) only
    intercepts dependencies resolved through Depends(); a direct Python
    call bypasses it entirely; found by test_agent_runs.py and
    test_onboarding_flow.py suddenly making real Gemini calls in CI-shaped
    test runs the moment this dependency existed at all."""
    return wrap_llm_provider_with_budget(provider, db, user_id, settings)


def get_search_provider(settings: Settings = Depends(get_settings)) -> SearchProvider:
    """Select the configured SearchProvider. Defaults to fake — never
    requires a live Tavily key unless SEARCH_PROVIDER is explicitly set."""
    if settings.search_provider == "tavily":
        if not settings.tavily_api_key:
            raise RuntimeError("SEARCH_PROVIDER=tavily requires TAVILY_API_KEY to be set")
        from app.providers.search.tavily import TavilySearchProvider

        return TavilySearchProvider(
            api_key=settings.tavily_api_key, timeout_seconds=settings.tavily_timeout_seconds
        )

    if settings.search_provider == "youtube":
        return get_youtube_provider(settings)

    if settings.search_provider == "combined":
        from app.providers.search.composite import CompositeSearchProvider
        from app.providers.search.tavily import TavilySearchProvider

        providers: list[SearchProvider] = [get_youtube_provider(settings)]
        if settings.tavily_api_key:
            providers.insert(
                0,
                TavilySearchProvider(
                    api_key=settings.tavily_api_key,
                    timeout_seconds=settings.tavily_timeout_seconds,
                ),
            )
        return CompositeSearchProvider(*providers)

    return FakeSearchProvider()


def get_youtube_provider(settings: Settings = Depends(get_settings)) -> SearchProvider:
    """Select the configured YouTubeMediaProvider."""
    from app.providers.search.youtube import YouTubeMediaProvider

    return YouTubeMediaProvider(
        api_key=settings.youtube_api_key, timeout_seconds=settings.youtube_timeout_seconds
    )


__all__ = [
    "get_db",
    "get_current_user_id",
    "get_llm_provider",
    "get_budgeted_llm_provider",
    "wrap_llm_provider_with_budget",
    "get_search_provider",
    "get_youtube_provider",
    "Depends",
    "Session",
]
