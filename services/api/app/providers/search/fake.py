from __future__ import annotations

from typing import Any

from app.providers.search.base import Document, SearchProvider


class FakeSearchProvider(SearchProvider):
  """Deterministic search stub for tests and M0 wiring."""

  def __init__(self, documents: list[Document] | None = None) -> None:
      self.documents = documents or [
          Document(
              title="Fixture article",
              url="https://example.com/fixture",
              extract="A short fixture extract for M0.",
              source="curated_fallback",
          )
      ]
      self.calls: list[dict[str, Any]] = []

  def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
      self.calls.append({"query": query, "opts": opts or {}})
      return list(self.documents)
