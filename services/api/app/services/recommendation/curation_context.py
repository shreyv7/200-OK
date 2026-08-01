"""Thread-local provider context for curation graph nodes — AIS M4."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from app.providers.llm.base import LLMProvider
from app.providers.llm.fake import FakeLLMProvider
from app.providers.search.base import SearchProvider
from app.providers.search.fake import FakeSearchProvider

_llm_var: ContextVar[LLMProvider | None] = ContextVar("curation_llm", default=None)
_search_var: ContextVar[SearchProvider | None] = ContextVar("curation_search", default=None)


def get_curation_llm() -> LLMProvider:
    return _llm_var.get() or FakeLLMProvider()


def get_curation_search() -> SearchProvider:
    return _search_var.get() or FakeSearchProvider()


@contextmanager
def curation_providers(
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
):
    """Inject providers for graph nodes without passing SDKs through graph state."""
    llm_token = _llm_var.set(llm)
    search_token = _search_var.set(search)
    try:
        yield
    finally:
        _llm_var.reset(llm_token)
        _search_var.reset(search_token)


def providers_from_state(state: dict[str, Any]) -> tuple[LLMProvider | None, SearchProvider | None]:
    """Optional explicit providers on graph state (tests)."""
    return state.get("llm_provider"), state.get("search_provider")
