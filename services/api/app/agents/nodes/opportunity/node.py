"""Real-World Opportunity lens — AIS M6."""

from __future__ import annotations

import logging
from typing import Any

from app.services.recommendation.badge_mapping import document_source_to_badge
from app.services.recommendation.curation_context import get_curation_search, providers_from_state
from app.services.recommendation.pune_events_fallback import get_pune_events_fallback

logger = logging.getLogger(__name__)


def build_opportunity_query(bottleneck: str) -> str:
    return f"{bottleneck} meetup workshop event Pune"


def _document_to_candidate(document: Any, index: int, bottleneck: str) -> dict[str, Any]:
    return {
        "id": f"cand-event-{index}",
        "type": "real_world_experience",
        "title": document.title,
        "url": document.url,
        "sourceBadge": document_source_to_badge(document.source),
        "tags": {"bottleneck": bottleneck, "stage": "early"},
    }


def retrieve_opportunity_candidates(
    bottleneck: str,
    *,
    search: Any | None = None,
) -> list[dict[str, Any]]:
    provider = search or get_curation_search()
    query = build_opportunity_query(bottleneck)
    try:
        documents = provider.search(query, {"limit": 3})
    except Exception as exc:  # noqa: BLE001
        logger.warning("Opportunity retrieval failed for %s: %s", bottleneck, exc)
        documents = []

    if documents:
        return [
            _document_to_candidate(doc, index, bottleneck) for index, doc in enumerate(documents)
        ]
    return get_pune_events_fallback(bottleneck)


def opportunity_node(state: dict[str, Any]) -> dict[str, Any]:
    bottleneck_packet = state.get("bottleneck_packet") or {}
    bottleneck = bottleneck_packet.get("bottleneck", "execution")
    _, search_override = providers_from_state(state)
    candidates = retrieve_opportunity_candidates(bottleneck, search=search_override)
    return {
        "visited": ["opportunity"],
        "opportunity_candidates": candidates,
    }
