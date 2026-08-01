"""Next Step retrieval lens — AIS M4."""

from __future__ import annotations

import logging
from typing import Any

from app.services.recommendation.badge_mapping import document_source_to_badge
from app.services.recommendation.curation_context import get_curation_search, providers_from_state
from app.services.recommendation.fallback_catalog import get_fallback_knowledge

logger = logging.getLogger(__name__)


def build_next_step_query(bottleneck: str) -> str:
    return f"smallest next step for {bottleneck} bottleneck personal growth"


def _document_to_candidate(document: Any, index: int) -> dict[str, Any]:
    badge = document_source_to_badge(document.source)
    return {
        "id": f"cand-media-{index}",
        "type": "media",
        "title": document.title,
        "url": document.url,
        "sourceBadge": badge,
        "extract": document.extract,
    }


def retrieve_knowledge_candidates(
    bottleneck: str,
    *,
    search: Any | None = None,
) -> list[dict[str, Any]]:
    """Call SearchProvider; never return an empty candidate list."""
    provider = search or get_curation_search()
    query = build_next_step_query(bottleneck)
    try:
        documents = provider.search(query, {"limit": 3})
    except Exception as exc:  # noqa: BLE001 — retrieval failure must not block curation
        logger.warning("Knowledge retrieval failed for %s: %s", bottleneck, exc)
        documents = []

    if not documents:
        return [get_fallback_knowledge(bottleneck)]

    return [_document_to_candidate(doc, index) for index, doc in enumerate(documents)]


def knowledge_node(state: dict[str, Any]) -> dict[str, Any]:
    bottleneck_packet = state.get("bottleneck_packet") or {}
    bottleneck = bottleneck_packet.get("bottleneck", "execution")
    _, search_override = providers_from_state(state)
    candidates = retrieve_knowledge_candidates(bottleneck, search=search_override)
    return {
        "visited": ["knowledge"],
        "knowledge_candidates": candidates,
    }
