"""Qdrant catalog retrieval helpers for Curator knowledge lens."""

from __future__ import annotations

from typing import Any

from app.providers.embeddings import EmbeddingProvider, get_embedding_provider
from app.providers.qdrant import QdrantVectorStore, get_vector_store


def retrieve_vector_catalog_candidates(
    query: str,
    *,
    store: QdrantVectorStore | None = None,
    embedder: EmbeddingProvider | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Search indexed catalog collections and shape hits as knowledge candidates."""
    vector_store = store or get_vector_store()
    if not vector_store.is_enabled:
        return []

    provider = embedder or get_embedding_provider()
    query_vector = provider.embed([query])[0]
    collections = ("catalog_stories", "catalog_tools", "catalog_mentors")
    hits: list[tuple[str, dict[str, Any]]] = []
    for collection in collections:
        for hit in vector_store.search(collection, query_vector=query_vector, limit=limit):
            hits.append((collection, hit))

    hits.sort(key=lambda item: item[1].get("score", 0.0), reverse=True)
    out: list[dict[str, Any]] = []
    for index, (collection, hit) in enumerate(hits[:limit]):
        payload = hit.get("payload") or {}
        title = payload.get("title") or payload.get("name") or "Catalog resource"
        extract = (
            payload.get("outcome")
            or payload.get("description")
            or payload.get("bio")
            or payload.get("identity_tag")
            or ""
        )
        out.append(
            {
                "id": f"cand-vector-{hit.get('id', index)}",
                "type": "media" if "stories" in collection else ("tool" if "tools" in collection else "mentor"),
                "title": title,
                "url": payload.get("url"),
                "sourceBadge": "Cached web",
                "extract": str(extract),
                "metadata": {
                    "collection": collection,
                    "score": hit.get("score"),
                    "vector": True,
                    **{k: v for k, v in payload.items() if k != "original_id"},
                },
            }
        )
    return out
