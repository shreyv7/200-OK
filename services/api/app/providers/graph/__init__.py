"""Graph provider interface and implementations. Owner: Backend & AIS."""

from __future__ import annotations

import logging

from app.core.config import Settings
from app.providers.graph.base import GraphProvider
from app.providers.graph.fake import FakeGraphProvider
from app.providers.graph.neo4j import Neo4jGraphProvider

__all__ = ["GraphProvider", "FakeGraphProvider", "Neo4jGraphProvider", "get_graph_provider"]

logger = logging.getLogger(__name__)


def get_graph_provider(settings: Settings) -> GraphProvider:
    """Settings-driven graph provider (fake or Neo4j with graceful fallback)."""
    provider = settings.graph_db_provider
    if provider == "neo4j":
        if not settings.neo4j_uri or not settings.neo4j_password:
            logger.warning(
                "GRAPH_DB_PROVIDER=neo4j missing NEO4J_URI/NEO4J_PASSWORD; using fake graph"
            )
            return FakeGraphProvider()
        try:
            graph = Neo4jGraphProvider(
                uri=settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            graph.execute_query("RETURN 1 AS ok")
            return graph
        except Exception as exc:  # noqa: BLE001 — keep API bootable without Neo4j
            logger.warning("Neo4j unavailable (%s); using fake graph", exc)
            return FakeGraphProvider()
    return FakeGraphProvider()
