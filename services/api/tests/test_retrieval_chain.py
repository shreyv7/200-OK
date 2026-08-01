from __future__ import annotations

import time
from typing import Any

from app.providers.search.base import Document, SearchProvider
from app.services.curation.retrieval_chain import search_with_fallback


class _InstantSearchProvider(SearchProvider):
    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents

    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
        return self.documents


class _SlowSearchProvider(SearchProvider):
    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
        time.sleep(2.0)
        return []


class _FailingSearchProvider(SearchProvider):
    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
        raise RuntimeError("simulated Tavily failure")


def _fallback(query: str) -> list[Document]:
    return [Document(title="Fallback", url="https://example.com/fb", extract="F", source="curated_fallback")]


def test_cache_hit_returns_cached_web_badge(db_session) -> None:
    query = "cache hit retrieval chain test"
    provider = _InstantSearchProvider(
        [Document(title="Live", url="https://example.com/live", extract="L", source="tavily")]
    )
    # Prime the cache first.
    docs, badge = search_with_fallback(db_session, query, provider, _fallback)
    assert badge == "Live web"

    docs2, badge2 = search_with_fallback(db_session, query, provider, _fallback)
    assert badge2 == "Cached web"
    assert docs2[0].title == "Live"


def test_live_success_returns_live_web_badge(db_session) -> None:
    query = "unique live success query"
    provider = _InstantSearchProvider(
        [Document(title="Fresh", url="https://example.com/fresh", extract="Fr", source="tavily")]
    )
    docs, badge = search_with_fallback(db_session, query, provider, _fallback)
    assert badge == "Live web"
    assert docs[0].title == "Fresh"


def test_timeout_falls_back_to_curated(db_session) -> None:
    query = "unique timeout query"
    docs, badge = search_with_fallback(
        db_session, query, _SlowSearchProvider(), _fallback, timeout_seconds=0.1
    )
    assert badge == "Curated fallback"
    assert docs[0].title == "Fallback"


def test_provider_exception_falls_back_to_curated(db_session) -> None:
    query = "unique exception query"
    docs, badge = search_with_fallback(db_session, query, _FailingSearchProvider(), _fallback)
    assert badge == "Curated fallback"
    assert docs[0].title == "Fallback"
