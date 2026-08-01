"""Real Neo4j Graph Provider utilizing neo4j Bolt driver.

Only module allowed to import neo4j driver.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.providers.graph.base import GraphProvider


class Neo4jGraphProvider(GraphProvider):
    def __init__(self, uri: str, auth: tuple[str, str]) -> None:
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(uri, auth=auth)
        except ImportError:
            raise ImportError(
                "The 'neo4j' package is required to use Neo4jGraphProvider. "
                "Install it via `pip install neo4j`."
            )

    def execute_query(
        self, cypher: str, parameters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

    def close(self) -> None:
        if hasattr(self, "_driver") and self._driver:
            self._driver.close()
