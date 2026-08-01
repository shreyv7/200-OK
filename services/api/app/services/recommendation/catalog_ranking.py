"""Deterministic catalog ranking by stage/bottleneck — AIS M6."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.recommendation.catalog import CatalogItem

BOTTLENECK_EXACT_SCORE = 1.0
BOTTLENECK_ADJACENT_SCORE = 0.3
STAGE_MATCH_SCORE = 0.5
JUSTIFICATION_MIN_BOTTLENECK_SCORE = 1.0

_ADJACENT_BOTTLENECKS: dict[str, set[str]] = {
    "execution": {"confidence", "consistency"},
    "confidence": {"execution", "communication"},
    "consistency": {"execution", "discipline"},
}


@dataclass(frozen=True)
class ScoredCatalogItem:
    item: CatalogItem
    score: float
    bottleneck_score: float


def _bottleneck_score(item: CatalogItem, bottleneck: str) -> float:
    tag = item.tags.get("bottleneck", "")
    if tag == bottleneck:
        return BOTTLENECK_EXACT_SCORE
    if bottleneck in _ADJACENT_BOTTLENECKS.get(tag, set()):
        return BOTTLENECK_ADJACENT_SCORE
    if tag in _ADJACENT_BOTTLENECKS.get(bottleneck, set()):
        return BOTTLENECK_ADJACENT_SCORE
    return 0.0


def rank_catalog_items(
    items: list[CatalogItem],
    *,
    bottleneck: str,
    stage: str,
) -> list[ScoredCatalogItem]:
    """Rank by bottleneck/stage fit — popularity is ignored."""
    scored: list[ScoredCatalogItem] = []
    for item in items:
        bottleneck_score = _bottleneck_score(item, bottleneck)
        total = bottleneck_score
        if item.tags.get("stage") == stage:
            total += STAGE_MATCH_SCORE
        scored.append(
            ScoredCatalogItem(item=item, score=total, bottleneck_score=bottleneck_score)
        )
    return sorted(scored, key=lambda row: (-row.score, row.item.id))


def select_catalog_element(
    scored: list[ScoredCatalogItem],
    *,
    min_bottleneck_score: float = JUSTIFICATION_MIN_BOTTLENECK_SCORE,
) -> CatalogItem | None:
    """Return the top justified catalog item or None (no filler)."""
    for row in scored:
        if row.bottleneck_score >= min_bottleneck_score:
            return row.item
    return None


def catalog_item_to_candidate(item: CatalogItem) -> dict:
    return {
        "id": item.id,
        "type": item.type,
        "title": item.title,
        "url": item.url,
        "sourceBadge": "Curated fallback",
        "tags": dict(item.tags),
        "starter_action": item.starter_action,
    }
