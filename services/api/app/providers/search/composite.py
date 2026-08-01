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
        return documents
