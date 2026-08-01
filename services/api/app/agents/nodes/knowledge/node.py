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


def score_developmental_fit(document: Any, bottleneck: str) -> float:
    """Score candidate documents for developmental fit based on bottleneck relevance and badge quality."""
    score = 0.0
    badge = document_source_to_badge(getattr(document, "source", "curated_fallback"))
    if badge == "Live web":
        score += 0.5
    elif badge == "Cached web":
        score += 0.4
    else:
        score += 0.1

    text = f"{getattr(document, 'title', '')} {getattr(document, 'extract', '')}".lower()
    if bottleneck.lower() in text:
        score += 0.3
    if any(k in text for k in ["guide", "strategy", "habit", "step", "focus", "action"]):
        score += 0.2

    return score


def _document_to_candidate(document: Any, index: int) -> dict[str, Any]:
    badge = document_source_to_badge(getattr(document, "source", "curated_fallback"))
    return {
        "id": f"cand-media-{index}",
        "type": "media",
        "title": getattr(document, "title", "Growth resource"),
        "url": getattr(document, "url", None),
        "sourceBadge": badge,
        "extract": getattr(document, "extract", ""),
        "metadata": getattr(document, "metadata", {}),
    }


def retrieve_knowledge_candidates(
    bottleneck: str,
    *,
    search: Any | None = None,
) -> list[dict[str, Any]]:
    """Call SearchProvider, rank by developmental fit; never return empty."""
    provider = search or get_curation_search()
    query = build_next_step_query(bottleneck)
    try:
        documents = provider.search(query, {"limit": 5})
    except Exception as exc:  # noqa: BLE001 — retrieval failure must not block curation
        logger.warning("Knowledge retrieval failed for %s: %s", bottleneck, exc)
        documents = []

    if not documents:
        return [get_fallback_knowledge(bottleneck)]

    ranked_docs = sorted(
        documents, key=lambda d: score_developmental_fit(d, bottleneck), reverse=True
    )
    return [_document_to_candidate(doc, index) for index, doc in enumerate(ranked_docs[:3])]


def knowledge_node(state: dict[str, Any]) -> dict[str, Any]:
    bottleneck_packet = state.get("bottleneck_packet") or {}
    bottleneck = bottleneck_packet.get("bottleneck", "execution")
    _, search_override = providers_from_state(state)
    candidates = retrieve_knowledge_candidates(bottleneck, search=search_override)
    return {
        "visited": ["knowledge"],
        "knowledge_candidates": candidates,
    }
