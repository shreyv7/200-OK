"""Next Step retrieval lens — AIS M4 (+ Qdrant catalog / Neo4j Graph RAG)."""

from __future__ import annotations

from typing import Any

from app.services.recommendation.curation_context import get_curation_search, providers_from_state
from app.services.recommendation.knowledge_retrieval import retrieve_knowledge_candidates


def knowledge_node(state: dict[str, Any]) -> dict[str, Any]:
    bottleneck_packet = state.get("bottleneck_packet") or {}
    bottleneck = bottleneck_packet.get("bottleneck", "execution")
    decision_packet = state.get("decision_packet") or {}
    ranking_features = decision_packet.get("rankingFeatures")
    _, search_override = providers_from_state(state)
    db_session = state.get("db_session")

    candidates = retrieve_knowledge_candidates(
        bottleneck,
        search=search_override or get_curation_search(),
        user_id=state.get("user_id"),
        db=db_session,
        ranking_features=ranking_features,
    )
    return {
        "visited": ["knowledge"],
        "knowledge_candidates": candidates,
    }
