"""Fake Graph Provider for deterministic tests and offline dev.

Provides in-memory graph stubs matching Cypher query structures.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.providers.graph.base import GraphProvider


class FakeGraphProvider(GraphProvider):
    """In-memory GraphProvider implementation for pytest and offline local dev."""

    def __init__(self, seeded_records: List[Dict[str, Any]] | None = None) -> None:
        self.seeded_records = seeded_records or []
        self.queries_run: List[Dict[str, Any]] = []

    def execute_query(
        self, cypher: str, parameters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        params = parameters or {}
        self.queries_run.append({"cypher": cypher, "parameters": params})

        # Return seeded records if available
        if self.seeded_records:
            return self.seeded_records

        # Default fallback response for test assertions
        return [
            {
                "resource_id": "seed-resource-1",
                "title": "Speaking in Public: The Essential Guide",
                "type": "media",
                "category": "learning",
                "difficulty_tier": "light",
                "extract": "Mastering the first 60 seconds of any presentation.",
                "bottleneck_title": "Confidence",
                "addressed_markers": ["Public Speaking"],
                "aligned_attributes": ["Confident Speaker"],
            }
        ]

    def close(self) -> None:
        pass
