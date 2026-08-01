"""Graph Database Repository for Cypher queries. Owner: Backend & AIS."""

from __future__ import annotations

from typing import Any, Dict, List

from app.providers.graph.base import GraphProvider


class GraphRepository:
    def __init__(self, provider: GraphProvider) -> None:
        self.provider = provider

    def upsert_user(self, user_id: str, demo_mode: bool = False) -> None:
        cypher = """
        MERGE (u:User {id: $userId})
        SET u.demo_mode = $demoMode
        """
        self.provider.execute_query(cypher, {"userId": user_id, "demoMode": demo_mode})

    def upsert_bottleneck(self, bottleneck_id: str, bottleneck_type: str, title: str) -> None:
        cypher = """
        MERGE (b:Bottleneck {id: $id})
        SET b.type = $type, b.title = $title
        """
        self.provider.execute_query(cypher, {"id": bottleneck_id, "type": bottleneck_type, "title": title})

    def link_user_bottleneck(self, user_id: str, bottleneck_type: str, confidence: float = 1.0) -> None:
        cypher = """
        MATCH (u:User {id: $userId})
        MATCH (b:Bottleneck {type: $type})
        MERGE (u)-[r:LIMITED_BY]->(b)
        SET r.confidence = $confidence
        """
        self.provider.execute_query(cypher, {"userId": user_id, "type": bottleneck_type, "confidence": confidence})

    def upsert_resource(
        self,
        resource_id: str,
        title: str,
        resource_type: str,
        category: str,
        difficulty_tier: str,
        extract: str,
        bottleneck_type: str | None = None,
    ) -> None:
        cypher = """
        MERGE (r:Resource {id: $id})
        SET r.title = $title,
            r.type = $type,
            r.category = $category,
            r.difficulty_tier = $difficultyTier,
            r.extract = $extract
        """
        self.provider.execute_query(
            cypher,
            {
                "id": resource_id,
                "title": title,
                "type": resource_type,
                "category": category,
                "difficultyTier": difficulty_tier,
                "extract": extract,
            },
        )
        if bottleneck_type:
            link_cypher = """
            MATCH (r:Resource {id: $id})
            MERGE (b:Bottleneck {type: $bottleneckType})
            MERGE (r)-[:TARGETS_BOTTLENECK]->(b)
            """
            self.provider.execute_query(link_cypher, {"id": resource_id, "bottleneckType": bottleneck_type})

    def get_candidates_for_bottleneck(
        self, user_id: str, bottleneck_type: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Multi-hop Graph RAG query retrieving resources matching user's active bottleneck."""
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

    def fulltext_search_resources(self, search_query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-Text RAG query over Resource node index."""
        cypher = """
        CALL db.index.fulltext.queryNodes("resource_fulltext_idx", $searchQuery) YIELD node AS r, score
        MATCH (r)-[:TARGETS_BOTTLENECK]->(b:Bottleneck)
        RETURN r.id AS resource_id,
               r.title AS title,
               r.type AS type,
               r.extract AS extract,
               b.title AS bottleneck,
               score
        ORDER BY score DESC
        LIMIT $limit
        """
        return self.provider.execute_query(cypher, {"searchQuery": search_query, "limit": limit})
