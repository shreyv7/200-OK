"""Seeded Next Step + micro-mission catalog — AIS M4 fallback path."""

from __future__ import annotations

from typing import Any

from app.schemas.bottleneck import BottleneckLabel

CatalogEntry = dict[str, Any]

_KNOWLEDGE: dict[BottleneckLabel, CatalogEntry] = {
    "execution": {
        "id": "fallback-media-execution",
        "type": "media",
        "title": "How to structure a one-minute talk",
        "url": "https://example.com/one-minute-talk",
        "sourceBadge": "Curated fallback",
    },
    "confidence": {
        "id": "fallback-media-confidence",
        "type": "media",
        "title": "Speaking anxiety: a 5-minute reset",
        "url": "https://example.com/speaking-reset",
        "sourceBadge": "Curated fallback",
    },
    "consistency": {
        "id": "fallback-media-consistency",
        "type": "knowledge",
        "title": "Build a 10-minute daily practice loop",
        "url": "https://example.com/daily-loop",
        "sourceBadge": "Curated fallback",
    },
}

_MISSIONS: dict[BottleneckLabel, CatalogEntry] = {
    "execution": {
        "id": "fallback-mission-execution",
        "type": "micro_mission",
        "title": "Ship a 60-second speaking clip",
        "sourceBadge": "Curated fallback",
    },
    "confidence": {
        "id": "fallback-mission-confidence",
        "type": "micro_mission",
        "title": "Record a 30-second voice note without editing",
        "sourceBadge": "Curated fallback",
    },
    "consistency": {
        "id": "fallback-mission-consistency",
        "type": "micro_mission",
        "title": "Block 10 minutes tomorrow for one rep",
        "sourceBadge": "Curated fallback",
    },
}

_DEFAULT_LABEL: BottleneckLabel = "execution"


def _normalize_label(bottleneck: str) -> BottleneckLabel:
    if bottleneck in _KNOWLEDGE:
        return bottleneck  # type: ignore[return-value]
    return _DEFAULT_LABEL


def get_fallback_knowledge(bottleneck: str) -> CatalogEntry:
    label = _normalize_label(bottleneck)
    return dict(_KNOWLEDGE[label])


def get_fallback_mission(bottleneck: str, *, small_experiment: bool = False) -> CatalogEntry:
    label = _normalize_label(bottleneck)
    mission = dict(_MISSIONS[label])
    if small_experiment:
        mission["title"] = f"Small experiment: {mission['title'].lower()}"
    return mission
