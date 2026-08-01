"""Catalog item shape + fetch seam — AIS M6."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

CatalogType = Literal["growth_story", "tool", "mentor", "real_world_experience"]


@dataclass(frozen=True)
class CatalogItem:
    id: str
    type: CatalogType
    title: str
    url: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    starter_action: str | None = None
    popularity: float = 0.0


class CatalogSource(Protocol):
    def fetch(self, *, bottleneck: str, stage: str) -> list[CatalogItem]:
        """Return catalog rows for ranking (Backend DB/API impl lands in M6)."""


_FIXTURE_CATALOG: list[CatalogItem] = [
    CatalogItem(
        id="story-execution-1",
        type="growth_story",
        title="From draft to stage: shipping despite fear",
        url="https://example.com/story-ship",
        tags={
            "identity": "public_speaker",
            "stage": "early",
            "bottleneck": "execution",
            "outcome": "published_first_talk",
        },
        popularity=999.0,
    ),
    CatalogItem(
        id="tool-execution-1",
        type="tool",
        title="Notion capture template for daily reps",
        url="https://notion.so",
        tags={
            "identity": "public_speaker",
            "stage": "early",
            "bottleneck": "execution",
            "outcome": "consistent_shipping",
        },
        starter_action="Log one rep before publishing.",
        popularity=500.0,
    ),
    CatalogItem(
        id="mentor-confidence-1",
        type="mentor",
        title="Priya — overcame public-speaking anxiety",
        url="https://example.com/mentor-priya",
        tags={
            "identity": "public_speaker",
            "stage": "early",
            "bottleneck": "confidence",
            "outcome": "regular_speaking",
        },
        popularity=800.0,
    ),
    CatalogItem(
        id="story-generic-1",
        type="growth_story",
        title="Generic motivation: believe in yourself",
        url="https://example.com/generic",
        tags={
            "identity": "general",
            "stage": "late",
            "bottleneck": "discipline",
            "outcome": "motivation",
        },
        popularity=10000.0,
    ),
]


class FixtureCatalogSource:
    """AIS test/demo catalog until Backend seeds land."""

    def __init__(self, items: list[CatalogItem] | None = None) -> None:
        self._items = items if items is not None else list(_FIXTURE_CATALOG)

    def fetch(self, *, bottleneck: str, stage: str) -> list[CatalogItem]:
        _ = stage
        return list(self._items)


def get_default_catalog_source() -> CatalogSource:
    return FixtureCatalogSource()
