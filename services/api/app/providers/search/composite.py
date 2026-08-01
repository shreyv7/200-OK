"""Composable retrieval provider used to blend web and YouTube candidates."""

from __future__ import annotations

from typing import Any

from app.providers.search.base import Document, SearchProvider


class CompositeSearchProvider(SearchProvider):
    def __init__(self, *providers: SearchProvider) -> None:
        self._providers = providers

    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
        documents: list[Document] = []
        seen_urls: set[str] = set()
        for provider in self._providers:
            try:
                for document in provider.search(query, opts):
                    if document.url not in seen_urls:
                        seen_urls.add(document.url)
                        documents.append(document)
            except Exception:
                # Individual providers must not make the retrieval chain empty.
                continue
        return documents or self.get_fallback(query)

    def get_fallback(self, query: str) -> list[Document]:
        documents: list[Document] = []
        seen_urls: set[str] = set()
        for provider in self._providers:
            fallback = getattr(provider, "get_fallback", None)
            if not callable(fallback):
                continue
            try:
                for document in fallback(query):
                    if document.url not in seen_urls:
                        seen_urls.add(document.url)
                        documents.append(document)
            except Exception:
                continue
        return documents
