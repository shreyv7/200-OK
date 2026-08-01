"""Seeded Next Step + micro-mission catalog — AIS M4 fallback path."""

from __future__ import annotations

from typing import Any

from app.schemas.bottleneck import BottleneckLabel
from app.services.recommendation.planner_missions import MISSION_TEMPLATES

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
    label: {
        "id": f"fallback-mission-{label}",
        "type": "micro_mission",
        "title": title,
        "sourceBadge": "Curated fallback",
    }
    for label, title in MISSION_TEMPLATES.items()
}

_DEFAULT_LABEL: BottleneckLabel = "execution"


def _normalize_knowledge_label(bottleneck: str) -> BottleneckLabel:
    if bottleneck in _KNOWLEDGE:
        return bottleneck  # type: ignore[return-value]
    return _DEFAULT_LABEL


def _normalize_mission_label(bottleneck: str) -> BottleneckLabel:
    if bottleneck in _MISSIONS:
        return bottleneck  # type: ignore[return-value]
    return _DEFAULT_LABEL


def get_fallback_knowledge(bottleneck: str) -> CatalogEntry:
    label = _normalize_knowledge_label(bottleneck)
    return dict(_KNOWLEDGE[label])


def get_fallback_mission(bottleneck: str, *, small_experiment: bool = False) -> CatalogEntry:
    label = _normalize_mission_label(bottleneck)
    mission = dict(_MISSIONS[label])
    if small_experiment:
        mission["title"] = f"Small experiment: {mission['title'].lower()}"
    return mission
