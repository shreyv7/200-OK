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
        if not settings.gemini_api_key:
            raise RuntimeError("LLM_PROVIDER=gemini requires GEMINI_API_KEY to be set")
        from app.providers.llm.gemini import GeminiLLMProvider

        return GeminiLLMProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)

    if settings.llm_provider == "bedrock":
        from app.providers.llm.bedrock import BedrockLLMProvider

        return BedrockLLMProvider(
            region=settings.bedrock_region, model_id=settings.bedrock_model_id
        )

    return FakeLLMProvider()


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
    "get_search_provider",
    "get_youtube_provider",
    "Depends",
    "Session",
]
