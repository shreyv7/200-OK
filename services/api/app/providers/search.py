"""SearchProvider interface. Owner: Backend scaffolds; AIS fills search.

No Tavily/YouTube SDK imports here or anywhere outside a future
`providers/search/` implementation module (hard constraint, guidelines.md §9.3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class Document(BaseModel):
    title: str
    url: str
    extract: str
    source: str


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, opts: dict[str, Any] | None = None) -> list[Document]:
        raise NotImplementedError
