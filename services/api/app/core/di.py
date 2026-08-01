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


__all__ = [
    "get_db",
    "get_current_user_id",
    "get_llm_provider",
    "Depends",
    "Session",
]
