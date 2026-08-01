"""EmbeddingProvider interface. Owner: Backend scaffolds; AIA/AIS fill usage patterns."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
