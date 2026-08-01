"""Seeded fallback resources. Owner: Backend. milestones.md M4.

Small static set used as the final link in the retrieval chain when
Tavily is unavailable/times out/quota-exhausted. Not a catalog (that's
M6's job) — just enough so a refresh never returns empty.
"""

from __future__ import annotations

from app.providers.search.base import Document

_FALLBACK_RESOURCES: list[Document] = [
    Document(
        title="How to structure a one-minute talk",
        url="https://example.com/one-minute-talk",
        extract="A short guide to structuring a confident one-minute talk.",
        source="curated_fallback",
    ),
    Document(
        title="Shipping your first public project",
        url="https://example.com/ship-first-project",
        extract="A practical checklist for publishing a small project publicly.",
        source="curated_fallback",
    ),
    Document(
        title="Overcoming the fear of being judged",
        url="https://example.com/fear-of-judgement",
        extract="Reframing techniques for creators afraid to publish their work.",
        source="curated_fallback",
    ),
]


def get_fallback_resources(query: str) -> list[Document]:
    """Returns the seeded fallback set — currently identity/bottleneck-agnostic,
    just enough to guarantee a non-empty result (milestones.md M4)."""
    return list(_FALLBACK_RESOURCES)
