"""Base abstract interface for Graph Database operations (Neo4j / Fake).

Isolates graph database calls behind DI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class GraphProvider(ABC):
    @abstractmethod
    def execute_query(
        self, cypher: str, parameters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """Executes a Cypher query with parameters and returns structured records."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Closes any underlying database connections or drivers."""
        raise NotImplementedError
