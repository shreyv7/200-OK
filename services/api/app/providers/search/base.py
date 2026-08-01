from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class Document(BaseModel):
  title: str
  url: str
  extract: str
  source: str
  metadata: dict[str, Any] = Field(default_factory=dict)


class SearchProvider(ABC):
  """Retrieval facade — cache → live → fallback chain lives in Backend adapter."""

  @abstractmethod
  def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
      """Return normalized search documents."""
