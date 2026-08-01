"""Graph Sync Service for projecting Postgres entities to Neo4j graph nodes.

Maintains idempotent graph state synced with system-of-record relational tables.
"""

from __future__ import annotations

from typing import Any, Dict

from app.repositories.graph_repository import GraphRepository


class GraphSyncService:
    def __init__(self, repo: GraphRepository) -> None:
        self.repo = repo

    def sync_user(self, user_id: str, demo_mode: bool = False) -> None:
        self.repo.upsert_user(user_id=user_id, demo_mode=demo_mode)

    def sync_bottleneck(self, user_id: str, bottleneck_type: str, title: str, confidence: float = 1.0) -> None:
        self.repo.upsert_bottleneck(bottleneck_id=f"bn-{bottleneck_type}", bottleneck_type=bottleneck_type, title=title)
        self.repo.link_user_bottleneck(user_id=user_id, bottleneck_type=bottleneck_type, confidence=confidence)

    def sync_resource(self, resource_data: Dict[str, Any]) -> None:
        self.repo.upsert_resource(
            resource_id=resource_data["id"],
            title=resource_data.get("title", "Untitled Resource"),
            resource_type=resource_data.get("type", "knowledge"),
            category=resource_data.get("category", "learning"),
            difficulty_tier=resource_data.get("difficulty_tier", "full"),
            extract=resource_data.get("extract", ""),
            bottleneck_type=resource_data.get("bottleneck_type"),
        )


def sync_user_graph(
    db: Any,
    user_id: str,
    *,
    provider: Any,
) -> dict[str, Any]:
    """Project user twin + active bottleneck into the graph store."""
    from app.repositories import twin_repository
    from app.repositories.graph_repository import GraphRepository

    repo = GraphRepository(provider)
    service = GraphSyncService(repo)
    service.sync_user(user_id)

    declared = twin_repository.get_active_declared_self(db, user_id)
    attributes_synced = len(declared.attributes) if declared is not None else 0
    bottleneck = "execution"

    service.sync_bottleneck(user_id, bottleneck, title=bottleneck.replace("_", " ").title())
    return {
        "userId": user_id,
        "bottleneck": bottleneck,
        "attributesSynced": attributes_synced,
        "resourcesSynced": 0,
        "provider": provider.__class__.__name__,
    }
