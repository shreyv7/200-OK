"""Production Knowledge retrieval — Tavily/cache/fallback + Qdrant + Graph RAG."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.providers.search.base import Document, SearchProvider
from app.services.curation.fallback_resources import get_fallback_resources
from app.services.curation.retrieval_chain import search_with_fallback
from app.services.recommendation.badge_mapping import document_source_to_badge
from app.services.recommendation.fallback_catalog import get_fallback_knowledge
from app.services.recommendation.graph_rag import graph_candidates_as_knowledge
from app.services.recommendation.vector_catalog import retrieve_vector_catalog_candidates

logger = logging.getLogger(__name__)


def build_next_step_query(
    bottleneck: str,
    ranking_features: dict[str, Any] | None = None,
) -> str:
    """Build a retrieval query from bottleneck (+ optional decision features)."""
    query = f"smallest next step for {bottleneck} bottleneck personal growth"
    if ranking_features:
        alignment = ranking_features.get("alignment")
        if alignment is not None:
            query += f" alignment {alignment}"
    return query


def score_developmental_fit(document: Document | Any, bottleneck: str) -> float:
    """Score candidate documents for developmental fit based on bottleneck relevance."""
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


def _document_to_candidate(
    document: Document | Any,
    index: int,
    *,
    source_badge: str | None = None,
) -> dict[str, Any]:
    badge = source_badge or document_source_to_badge(getattr(document, "source", "curated_fallback"))
    return {
        "id": f"cand-media-{index}",
        "type": "media",
        "title": getattr(document, "title", "Growth resource"),
        "url": getattr(document, "url", None),
        "sourceBadge": badge,
        "extract": getattr(document, "extract", ""),
        "metadata": getattr(document, "metadata", {}),
    }


def _search_documents(
    query: str,
    *,
    search: SearchProvider,
    db: Session | None,
) -> tuple[list[Document], str | None]:
    """Production path uses Backend cache→live→fallback; tests may omit db."""
    if db is not None:
        documents, chain_badge = search_with_fallback(db, query, search, get_fallback_resources)
        return documents, chain_badge

    try:
        return search.search(query, {"limit": 5}), None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Knowledge retrieval failed for query %s: %s", query, exc)
        return [], None


def retrieve_knowledge_candidates(
    bottleneck: str,
    *,
    search: SearchProvider,
    user_id: str | None = None,
    db: Session | None = None,
    ranking_features: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Blend web/cache search, Qdrant catalog, and Graph RAG; never return empty."""
    query = build_next_step_query(bottleneck, ranking_features)
    documents, chain_badge = _search_documents(query, search=search, db=db)

    candidates: list[dict[str, Any]] = []
    if documents:
        ranked_docs = sorted(
            documents, key=lambda doc: score_developmental_fit(doc, bottleneck), reverse=True
        )
        candidates.extend(
            _document_to_candidate(doc, index, source_badge=chain_badge)
            for index, doc in enumerate(ranked_docs[:3])
        )

    try:
        vector_hits = retrieve_vector_catalog_candidates(query, limit=2)
        candidates.extend(vector_hits)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Qdrant catalog retrieval failed for %s: %s", bottleneck, exc)

    if user_id:
        try:
            graph_hits = graph_candidates_as_knowledge(user_id, bottleneck, limit=2)
            candidates.extend(graph_hits)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Graph RAG retrieval failed for %s: %s", bottleneck, exc)

    if not candidates:
        return [get_fallback_knowledge(bottleneck)]

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for cand in candidates:
        key = str(cand.get("title", "")).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(cand)
    return deduped[:5]
