"""Real Tavily search provider. Owner: Backend.

Only file allowed to import the Tavily SDK/client (hard constraint,
guidelines.md §9.3). Hard 1.5s timeout per prd.md §8 retrieval fallback
logic — callers (retrieval_chain.py) treat any exception, including a
timeout, as "fall through to seeded fallback", not a hard failure.
"""

from __future__ import annotations

from typing import Any

from app.providers.search.base import Document, SearchProvider


class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str, timeout_seconds: float = 1.5) -> None:
        from tavily import TavilyClient

        self._client = TavilyClient(api_key=api_key)
        self._timeout_seconds = timeout_seconds

    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
        response = self._client.search(query, timeout=self._timeout_seconds, **(opts or {}))
        if not isinstance(response, dict):
            return []
        results = response.get("results", [])
        if not isinstance(results, list):
            return []

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
        return documents


