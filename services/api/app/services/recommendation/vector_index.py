"""Catalog → Qdrant indexing (shared by API route and seed worker)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.providers.embeddings import EmbeddingProvider, get_embedding_provider
from app.providers.qdrant import QdrantVectorStore, get_vector_store
from app.repositories import catalog_repository


def index_catalog_to_qdrant(
    db: Session,
    *,
    embedder: EmbeddingProvider | None = None,
    store: QdrantVectorStore | None = None,
) -> dict[str, Any]:
    vector_store = store or get_vector_store()
    if not vector_store.is_enabled:
        return {"status": "error", "message": "Qdrant Vector Store is not active or connected"}

    provider = embedder or get_embedding_provider()
    indexed_counts: dict[str, int] = {}

    stories = catalog_repository.list_stories(db)
    if stories:
        points = []
        for s in stories:
            text = (
                f"{s.title} {' '.join(s.identityTags)} {' '.join(s.stageTags)} "
                f"{' '.join(s.bottleneckTags)} {s.summary} {s.outcome}"
            )
            vec = provider.embed([text])[0]
            points.append(
                {
                    "id": s.id,
                    "vector": vec,
                    "payload": {
                        "title": s.title,
                        "identity_tag": ",".join(s.identityTags),
                        "stage": ",".join(s.stageTags),
                        "bottleneck": ",".join(s.bottleneckTags),
                        "outcome": s.outcome,
                        "summary": s.summary,
                    },
                }
            )
        vector_store.upsert_points(
            "catalog_stories", points, vector_size=len(points[0]["vector"])
        )
        indexed_counts["catalog_stories"] = len(points)

    tools = catalog_repository.list_tools(db)
    if tools:
        points = []
        for t in tools:
            text = (
                f"{t.name} {' '.join(t.stageTags)} {' '.join(t.bottleneckTags)} "
                f"{t.description} {t.starterAction}"
            )
            vec = provider.embed([text])[0]
            points.append(
                {
                    "id": t.id,
                    "vector": vec,
                    "payload": {
                        "name": t.name,
                        "stage": ",".join(t.stageTags),
                        "bottleneck": ",".join(t.bottleneckTags),
                        "description": t.description,
                        "url": t.url,
                    },
                }
            )
        vector_store.upsert_points(
            "catalog_tools", points, vector_size=len(points[0]["vector"])
        )
        indexed_counts["catalog_tools"] = len(points)

    mentors = catalog_repository.list_mentors(db)
    if mentors:
        points = []
        for m in mentors:
            text = (
                f"{m.name} {' '.join(m.strengths)} {' '.join(m.stageTags)} "
                f"{' '.join(m.bottleneckTags)} {m.journey}"
            )
            vec = provider.embed([text])[0]
            points.append(
                {
                    "id": m.id,
                    "vector": vec,
                    "payload": {
                        "name": m.name,
                        "title": m.name,
                        "identity_tag": ",".join(m.strengths),
                        "stage": ",".join(m.stageTags),
                        "bottleneck": ",".join(m.bottleneckTags),
                        "bio": m.journey,
                    },
                }
            )
        vector_store.upsert_points(
            "catalog_mentors", points, vector_size=len(points[0]["vector"])
        )
        indexed_counts["catalog_mentors"] = len(points)

    return {
        "status": "success",
        "message": "Successfully indexed catalog into Qdrant Cloud",
        "counts": indexed_counts,
    }
