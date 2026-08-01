"""EmbeddingProvider interface. Owner: Backend scaffolds; AIA/AIS fill usage patterns."""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _hash_vector(tokens: list[str], *, dims: int = 32) -> list[float]:
    if not tokens:
        return [0.0] * dims
    vector = [0.0] * dims
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for index in range(dims):
            vector[index] += digest[index % len(digest)] / 255.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


class FakeEmbeddingProvider(EmbeddingProvider):
    """Offline, deterministic vectors — no network calls."""

    def __init__(self, *, dims: int = 32) -> None:
        self.dims = dims
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [_hash_vector(_tokenize(text), dims=self.dims) for text in texts]
