"""EmbeddingProvider interface and implementations."""

from __future__ import annotations

import hashlib
import logging
import math
import re
from abc import ABC, abstractmethod

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    dims: int

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


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini text embeddings via google.genai.

    Uses gemini-embedding-001 (3072-dim) by default. Rotates keys across pool
    and retries on rate limits or API errors.
    """

    DEFAULT_DIMS = 3072

    def __init__(self, api_keys: list[str], model: str = "gemini-embedding-001") -> None:
        if not api_keys:
            raise RuntimeError("GeminiEmbeddingProvider requires at least one API key")
        self._api_keys = api_keys
        self._model = model
        self.dims = self.DEFAULT_DIMS
        self._clients: list[object] | None = None
        self._next = 0

    def _get_clients(self) -> list[object]:
        if self._clients is None:
            from google import genai

            self._clients = [genai.Client(api_key=key) for key in self._api_keys]
        return self._clients

    def _embed_single(self, text: str) -> list[float]:
        clients = self._get_clients()
        last_exc: Exception | None = None
        start = self._next
        self._next = (self._next + 1) % len(clients)
        order = clients[start:] + clients[:start]

        for client in order:
            try:
                result = client.models.embed_content(model=self._model, contents=text)
                embedding = None
                if hasattr(result, "embeddings") and result.embeddings:
                    embedding = result.embeddings[0].values
                elif hasattr(result, "embedding") and result.embedding is not None:
                    embedding = getattr(result.embedding, "values", result.embedding)
                if embedding is None:
                    raise RuntimeError(f"Gemini embedding response missing vector for model={self._model}")
                return [float(v) for v in embedding]
            except Exception as exc:
                last_exc = exc
                logger.warning("Gemini embedding attempt failed for model=%s: %s", self._model, exc)
                continue

        if last_exc is not None:
            raise RuntimeError(f"All Gemini embedding API keys exhausted: {last_exc}") from last_exc
        raise RuntimeError("No healthy Gemini API key available for embedding")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for text in texts:
            vector = self._embed_single(text)
            self.dims = len(vector)
            vectors.append(vector)
        return vectors


def get_embedding_provider(
    settings: Settings | None = None,
    *,
    dims: int | None = None,
) -> EmbeddingProvider:
    """Settings-driven embedding factory. Defaults to fake hash vectors."""
    cfg = settings or get_settings()
    if cfg.embedding_provider == "gemini":
        keys = cfg.gemini_api_key_pool()
        if not keys:
            raise RuntimeError(
                "EMBEDDING_PROVIDER=gemini requires GEMINI_API_KEY or GEMINI_API_KEYS"
            )
        try:
            return GeminiEmbeddingProvider(api_keys=keys, model=cfg.embedding_model)
        except Exception as exc:  # noqa: BLE001 — keep API bootable without genai
            logger.warning("Gemini embedding provider unavailable (%s); using fake", exc)
    return FakeEmbeddingProvider(dims=dims if dims is not None else cfg.embedding_dims)
