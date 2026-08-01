"""Qdrant Cloud Vector Database provider module."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantClient = None  # type: ignore
    models = None  # type: ignore


class QdrantVectorStore:
    """Qdrant Vector Database service provider."""

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        prefix: str = "trellis",
    ) -> None:
        settings = get_settings()
        self.url = url or settings.qdrant_url
        self.api_key = api_key or settings.qdrant_api_key
        self.prefix = prefix or settings.qdrant_collection_prefix
        self.client: Any = None
        self._enabled = False

        # VECTOR_DB_PROVIDER=fake keeps CI/local deterministic even if a URL is set.
        if settings.vector_db_provider != "qdrant":
            return

        if QDRANT_AVAILABLE and self.url:
            try:
                self.client = QdrantClient(url=self.url, api_key=self.api_key, timeout=10.0)
                self._enabled = True
            except Exception as exc:
                logger.warning("Failed to connect to Qdrant Cloud: %s", exc)

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self.client is not None

    def collection_name(self, name: str) -> str:
        return f"{self.prefix}_{name}"

    def ensure_collection(self, name: str, vector_size: int = 32) -> bool:
        """Ensure collection exists in Qdrant with given vector size."""
        if not self.is_enabled:
            return False
        full_name = self.collection_name(name)
        try:
            collections = self.client.get_collections().collections
            existing = [c.name for c in collections]
            if full_name not in existing:
                self.client.create_collection(
                    collection_name=full_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE,
                    ),
                )
                logger.info("Created Qdrant collection: %s", full_name)
            return True
        except Exception as exc:
            logger.error("Error ensuring Qdrant collection %s: %s", full_name, exc)
            return False

    def upsert_points(
        self,
        collection: str,
        points: list[dict[str, Any]],
        vector_size: int = 32,
    ) -> bool:
        """Upsert points into collection.

        points format: [{"id": str, "vector": list[float], "payload": dict}]
        """
        if not self.is_enabled or not points:
            return False
        full_name = self.collection_name(collection)
        self.ensure_collection(collection, vector_size=vector_size)
        try:
            qdrant_points = []
            for item in points:
                raw_id = str(item.get("id") or uuid.uuid4())
                try:
                    point_id = str(uuid.UUID(raw_id))
                except ValueError:
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_id))

                qdrant_points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=item["vector"],
                        payload={"original_id": raw_id, **item.get("payload", {})},
                    )
                )
            self.client.upsert(collection_name=full_name, points=qdrant_points)
            logger.info("Upserted %d points to Qdrant collection %s", len(qdrant_points), full_name)
            return True
        except Exception as exc:
            logger.error("Error upserting points to Qdrant collection %s: %s", full_name, exc)
            return False

    def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search points in Qdrant collection by vector similarity."""
        if not self.is_enabled:
            return []
        full_name = self.collection_name(collection)
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if full_name not in collections:
                return []

            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=full_name,
                    query=query_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                )
                results = getattr(response, "points", response)
            elif hasattr(self.client, "search"):
                results = self.client.search(
                    collection_name=full_name,
                    query_vector=query_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                )
            else:
                results = []

            output = []
            for res in results:
                payload = getattr(res, "payload", {}) or {}
                score = getattr(res, "score", 0.0)
                original_id = payload.get("original_id") if isinstance(payload, dict) else str(getattr(res, "id", ""))
                output.append(
                    {
                        "id": original_id or str(getattr(res, "id", "")),
                        "score": round(float(score), 4),
                        "payload": payload,
                    }
                )
            return output
        except Exception as exc:
            logger.error("Error searching Qdrant collection %s: %s", full_name, exc)
            return []


_vector_store_instance: QdrantVectorStore | None = None


def get_vector_store() -> QdrantVectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = QdrantVectorStore()
    return _vector_store_instance
