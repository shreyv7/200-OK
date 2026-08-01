"""Vector & Semantic Search API Endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.di import get_current_user_id, get_db, get_embedding_provider, get_vector_store
from app.providers.embeddings import EmbeddingProvider
from app.providers.qdrant import QdrantVectorStore
from app.services.recommendation.vector_index import index_catalog_to_qdrant

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
def get_search_status(
    _user_id: str = Depends(get_current_user_id),
    store: QdrantVectorStore = Depends(get_vector_store),
) -> QdrantStatusResponse:
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
    embedder: EmbeddingProvider = Depends(get_embedding_provider),
    store: QdrantVectorStore = Depends(get_vector_store),
) -> SemanticSearchResponse:
    query_vector = embedder.embed([q])[0]

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
    embedder: EmbeddingProvider = Depends(get_embedding_provider),
    store: QdrantVectorStore = Depends(get_vector_store),
) -> dict[str, Any]:
    """Index all catalog items (stories, tools, mentors) into Qdrant Cloud."""
    return index_catalog_to_qdrant(db, embedder=embedder, store=store)
