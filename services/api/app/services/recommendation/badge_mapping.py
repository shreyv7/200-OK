"""Map SearchProvider document sources to stack source badges — AIS M4."""

from __future__ import annotations

from app.schemas.stack import SourceBadge


def document_source_to_badge(source: str) -> SourceBadge:
    normalized = source.lower().replace("_", " ").strip()
    if "live" in normalized or "youtube" in normalized:
        return "Live web"
    if "cache" in normalized:
        return "Cached web"
    return "Curated fallback"


