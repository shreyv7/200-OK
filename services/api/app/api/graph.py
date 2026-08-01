"""Neo4j Graph RAG API — status, sync, and bottleneck retrieval."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.di import get_current_user_id, get_db, get_graph_provider
from app.providers.graph.base import GraphProvider
from app.services.graph.sync_service import sync_user_graph
from app.services.recommendation.graph_rag import get_graph_rag_service

router = APIRouter(prefix="/graph", tags=["graph"])


class GraphStatusResponse(BaseModel):
    enabled: bool
    provider: str
    uri: str | None


class GraphSyncResponse(BaseModel):
    userId: str
    bottleneck: str
    attributesSynced: int
    resourcesSynced: int
    provider: str


class GraphRetrieveResponse(BaseModel):
    user_id: str
    bottleneck_type: str
    graph_candidates: list[dict[str, Any]]
    formatted_graph_context: str


@router.get("/status", response_model=GraphStatusResponse)
def graph_status(
    settings: Settings = Depends(get_settings),
    provider: GraphProvider = Depends(get_graph_provider),
    _user_id: str = Depends(get_current_user_id),
) -> GraphStatusResponse:
    return GraphStatusResponse(
        enabled=provider.is_enabled and settings.graph_db_provider == "neo4j",
        provider=settings.graph_db_provider,
        uri=settings.neo4j_uri,
    )


@router.post("/sync", response_model=GraphSyncResponse)
def graph_sync(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    provider: GraphProvider = Depends(get_graph_provider),
) -> GraphSyncResponse:
    result = sync_user_graph(db, user_id, provider=provider)
    return GraphSyncResponse(**result)


@router.get("/retrieve", response_model=GraphRetrieveResponse)
def graph_retrieve(
    bottleneck: str = Query(..., min_length=1),
    user_id: str = Depends(get_current_user_id),
    provider: GraphProvider = Depends(get_graph_provider),
) -> GraphRetrieveResponse:
    context = get_graph_rag_service(provider).retrieve_graph_context(user_id, bottleneck)
    return GraphRetrieveResponse(**context)
