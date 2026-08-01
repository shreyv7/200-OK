"""Curated Pune events fallback — AIS M6 Opportunity lens."""

from __future__ import annotations

from typing import Any

_PUNE_EVENTS: list[dict[str, Any]] = [
    {
        "id": "pune-toastmasters-1",
        "type": "real_world_experience",
        "title": "Pune Toastmasters Club — open house",
        "url": "https://example.com/pune-toastmasters",
        "sourceBadge": "Curated fallback",
        "tags": {"bottleneck": "confidence", "stage": "early", "location": "Pune"},
    },
    {
        "id": "pune-speaker-meetup-1",
        "type": "real_world_experience",
        "title": "Pune Speaker Practice Meetup",
        "url": "https://example.com/pune-speakers",
        "sourceBadge": "Curated fallback",
        "tags": {"bottleneck": "execution", "stage": "early", "location": "Pune"},
    },
]


def get_pune_events_fallback(bottleneck: str) -> list[dict[str, Any]]:
    """Return labeled Pune events; prefer bottleneck-tagged entries."""
    matched = [event for event in _PUNE_EVENTS if event["tags"].get("bottleneck") == bottleneck]
    if matched:
        return [dict(event) for event in matched]
    return [dict(event) for event in _PUNE_EVENTS]
