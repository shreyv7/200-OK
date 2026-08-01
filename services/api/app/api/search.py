"""Vector & Semantic Search API Endpoints."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db
from app.providers.embeddings import get_embedding_provider
from app.providers.qdrant import get_vector_store
from app.repositories import catalog_repository

router = APIRouter(tags=["search"])


class VectorSearchResultItem(BaseModel):
    id: str
    collection: str
    score: float
    payload: dict[str, Any]


class SemanticSearchResponse(BaseModel):
    query: str
    total_results: int
    vector_store_active: bool
    results: list[VectorSearchResultItem]


class QdrantStatusResponse(BaseModel):
    enabled: bool
    url: str | None
    collection_prefix: str
    collections: list[str]


@router.get("/search/status", response_model=QdrantStatusResponse)
def get_search_status(_user_id: str = Depends(get_current_user_id)) -> QdrantStatusResponse:
    store = get_vector_store()
    collections: list[str] = []
    if store.is_enabled:
        try:
            col_objs = store.client.get_collections().collections
            collections = [c.name for c in col_objs]
        except Exception:
            pass
    return QdrantStatusResponse(
        enabled=store.is_enabled,
        url=store.url,
        collection_prefix=store.prefix,
        collections=collections,
    )


@router.get("/search/semantic", response_model=SemanticSearchResponse)
def semantic_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    collection: str = Query("all", description="Target collection or 'all'"),
    limit: int = Query(5, ge=1, le=50),
    _user_id: str = Depends(get_current_user_id),
) -> SemanticSearchResponse:
    embedder = get_embedding_provider()
    query_vector = embedder.embed([q])[0]
    store = get_vector_store()

    target_collections = (
        ["catalog_stories", "catalog_tools", "catalog_mentors", "partner_profiles"]
        if collection == "all"
        else [collection]
    )

    results: list[VectorSearchResultItem] = []
    if store.is_enabled:
        for col in target_collections:
            hits = store.search(col, query_vector=query_vector, limit=limit)
            for hit in hits:
                results.append(
                    VectorSearchResultItem(
                        id=hit["id"],
                        collection=col,
                        score=hit["score"],
                        payload=hit["payload"],
                    )
                )
        results.sort(key=lambda x: x.score, reverse=True)
        results = results[:limit]

    return SemanticSearchResponse(
        query=q,
        total_results=len(results),
        vector_store_active=store.is_enabled,
        results=results,
    )


@router.post("/search/vector/index")
def reindex_vector_catalog(
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Index all catalog items (stories, tools, mentors) into Qdrant Cloud."""
    store = get_vector_store()
    if not store.is_enabled:
        return {"status": "error", "message": "Qdrant Vector Store is not active or connected"}

    embedder = get_embedding_provider()
    indexed_counts = {}

    # 1. Stories
    stories = catalog_repository.list_stories(db)
    if stories:
        points = []
        for s in stories:
            text = f"{s.title} {s.identity_tag} {s.stage} {s.bottleneck} {s.narrative}"
            vec = embedder.embed([text])[0]
            points.append(
                {
                    "id": s.id,
                    "vector": vec,
                    "payload": {
                        "title": s.title,
                        "identity_tag": s.identity_tag,
                        "stage": s.stage,
                        "bottleneck": s.bottleneck,
                        "outcome": s.outcome,
                    },
                }
            )
        store.upsert_points("catalog_stories", points, vector_size=len(points[0]["vector"]))
        indexed_counts["catalog_stories"] = len(points)

    # 2. Tools
    tools = catalog_repository.list_tools(db)
    if tools:
        points = []
        for t in tools:
            text = f"{t.name} {t.category} {t.stage} {t.bottleneck} {t.description}"
            vec = embedder.embed([text])[0]
            points.append(
                {
                    "id": t.id,
                    "vector": vec,
                    "payload": {
                        "name": t.name,
                        "category": t.category,
                        "stage": t.stage,
                        "bottleneck": t.bottleneck,
                        "url": t.url,
                    },
                }
            )
        store.upsert_points("catalog_tools", points, vector_size=len(points[0]["vector"]))
        indexed_counts["catalog_tools"] = len(points)

    # 3. Mentors
    mentors = catalog_repository.list_mentors(db)
    if mentors:
        points = []
        for m in mentors:
            text = f"{m.name} {m.title} {m.identity_tag} {m.stage} {m.bottleneck} {m.bio}"
            vec = embedder.embed([text])[0]
            points.append(
                {
                    "id": m.id,
                    "vector": vec,
                    "payload": {
                        "name": m.name,
                        "title": m.title,
                        "identity_tag": m.identity_tag,
                        "stage": m.stage,
                        "bottleneck": m.bottleneck,
                    },
                }
            )
        store.upsert_points("catalog_mentors", points, vector_size=len(points[0]["vector"]))
        indexed_counts["catalog_mentors"] = len(points)

    return {
        "status": "success",
        "message": "Successfully indexed catalog into Qdrant Cloud",
        "counts": indexed_counts,
    }
