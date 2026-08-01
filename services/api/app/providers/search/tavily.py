"""Real Tavily search provider. Owner: Backend.

Only file allowed to import the Tavily SDK/client (hard constraint,
guidelines.md §9.3). Hard 1.5s timeout per prd.md §8 retrieval fallback
logic — callers treat any exception, including a timeout, as "fall through
to seeded fallback", not a hard failure. This provider never raises.
"""

from __future__ import annotations

from typing import Any

from app.providers.search.base import Document, SearchProvider

_CURATED_WEB_FALLBACKS: list[Document] = [
    Document(
        title="Deep work: rules for focused success",
        url="https://www.calnewport.com/blog/2016/02/29/deep-work-rules-for-focused-success-in-a-distracted-world/",
        extract="Practical framing for protecting attention and building craft.",
        source="curated_web_fallback",
    ),
    Document(
        title="How to build a second brain",
        url="https://fortelabs.com/blog/basboverview/",
        extract="Capture, organize, and distill knowledge so ideas compound.",
        source="curated_web_fallback",
    ),
    Document(
        title="Maker's Schedule, Manager's Schedule",
        url="https://www.paulgraham.com/makersschedule.html",
        extract="Why context switches destroy deep creative work.",
        source="curated_web_fallback",
    ),
]


class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str | None, timeout_seconds: float = 1.5) -> None:
        self._timeout_seconds = timeout_seconds
        self._client = None
        if api_key and api_key.strip():
            try:
                from tavily import TavilyClient

                self._client = TavilyClient(api_key=api_key.strip())
            except Exception:
                self._client = None

    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
        if self._client is None:
            return self.get_fallback(query)

        try:
            response = self._client.search(
                query, timeout=self._timeout_seconds, **(opts or {})
            )
        except Exception:
            return self.get_fallback(query)

        if not isinstance(response, dict):
            return self.get_fallback(query)
        results = response.get("results", [])
        if not isinstance(results, list) or not results:
            return self.get_fallback(query)

        documents: list[Document] = []
        for r in results:
            if not isinstance(r, dict):
                continue
            title = r.get("title")
            url = r.get("url")
            content = r.get("content")
            if title and url and content:
                documents.append(
                    Document(
                        title=str(title),
                        url=str(url),
                        extract=str(content),
                        source="tavily_live",
                    )
                )
        return documents or self.get_fallback(query)

    def get_fallback(self, query: str) -> list[Document]:
        return list(_CURATED_WEB_FALLBACKS)
