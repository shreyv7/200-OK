"""Live Neo4j GraphProvider. Owner: Backend."""

from __future__ import annotations

import logging
from typing import Any

from app.providers.graph.base import GraphProvider

logger = logging.getLogger(__name__)


class Neo4jGraphProvider(GraphProvider):
    def __init__(self, uri: str, auth: tuple[str, str]) -> None:
        from neo4j import GraphDatabase

        self._uri = uri
        self._driver = GraphDatabase.driver(uri, auth=auth)
        self._enabled = True
        try:
            self._driver.verify_connectivity()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Neo4j connectivity check failed (%s); provider stays enabled for retries", exc)

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self._driver is not None

    def execute_query(
        self, cypher: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

    def close(self) -> None:
        if hasattr(self, "_driver") and self._driver:
            self._driver.close()
