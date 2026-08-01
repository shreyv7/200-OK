"""Neo4j Graph & Text RAG Implementation Code.

This file contains the complete, self-contained Python implementation for
Neo4j Graph Database operations and Graph-Augmented RAG context construction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class GraphProvider(ABC):
    @abstractmethod
    def execute_query(
        self, cypher: str, parameters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class Neo4jGraphProvider(GraphProvider):
    def __init__(self, uri: str, auth: tuple[str, str]) -> None:
        from neo4j import GraphDatabase
        self._driver = GraphDatabase.driver(uri, auth=auth)

    def execute_query(
        self, cypher: str, parameters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

    def close(self) -> None:
        if hasattr(self, "_driver") and self._driver:
            self._driver.close()


class FakeGraphProvider(GraphProvider):
    def __init__(self, seeded_records: List[Dict[str, Any]] | None = None) -> None:
        self.seeded_records = seeded_records or []
        self.queries_run: List[Dict[str, Any]] = []

    def execute_query(
        self, cypher: str, parameters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        self.queries_run.append({"cypher": cypher, "parameters": parameters or {}})
        if self.seeded_records:
            return self.seeded_records
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


class GraphRepository:
    def __init__(self, provider: GraphProvider) -> None:
        self.provider = provider

    def get_candidates_for_bottleneck(
        self, user_id: str, bottleneck_type: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        cypher = """
        MATCH (u:User {id: $userId})-[l:LIMITED_BY]->(b:Bottleneck {type: $bottleneckType})
        MATCH (r:Resource)-[:TARGETS_BOTTLENECK]->(b)
        WHERE NOT EXISTS {
            MATCH (u)-[d:DISMISSED]->(hf:HypothesisFamily)
            WHERE d.count >= 3 AND r.type = hf.lens_type
        }
        OPTIONAL MATCH (r)-[:ADDRESSES_MARKER]->(m:BehavioralMarker)<-[:MANIFESTS_VIA]-(a:IdentityAttribute)<-[:DECLARED]-(u)
        RETURN r.id AS resource_id,
               r.title AS title,
               r.type AS type,
               r.category AS category,
               r.difficulty_tier AS difficulty_tier,
               r.extract AS extract,
               b.title AS bottleneck_title,
               collect(DISTINCT m.name) AS addressed_markers,
               collect(DISTINCT a.name) AS aligned_attributes
        ORDER BY size(addressed_markers) DESC, r.title ASC
        LIMIT $limit
        """
        return self.provider.execute_query(
            cypher, {"userId": user_id, "bottleneckType": bottleneck_type, "limit": limit}
        )


class GraphRAGService:
    def __init__(self, repo: GraphRepository) -> None:
        self.repo = repo

    def retrieve_graph_context(
        self, user_id: str, bottleneck_type: str
    ) -> Dict[str, Any]:
        candidates = self.repo.get_candidates_for_bottleneck(
            user_id=user_id, bottleneck_type=bottleneck_type, limit=10
        )
        context_facts = []
        for candidate in candidates:
            markers = ", ".join(candidate.get("addressed_markers", [])) or "General Growth"
            attributes = ", ".join(candidate.get("aligned_attributes", [])) or "Target Identity"
            fact = (
                f"- Candidate [{candidate.get('type', 'resource').upper()}]: \"{candidate.get('title')}\"\n"
                f"  Targets Bottleneck: {candidate.get('bottleneck_title')}\n"
                f"  Addresses Markers: {markers}\n"
                f"  Aligned Attributes: {attributes}\n"
                f"  Summary Extract: {candidate.get('extract')}"
            )
            context_facts.append(fact)

        formatted_context = "\n\n".join(context_facts) if context_facts else "No graph facts retrieved."

        return {
            "user_id": user_id,
            "bottleneck_type": bottleneck_type,
            "graph_candidates": candidates,
            "formatted_graph_context": formatted_context,
        }
