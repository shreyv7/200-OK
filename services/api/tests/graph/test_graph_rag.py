"""Tests for Neo4j Graph Provider and Graph RAG Service."""

import unittest

from app.providers.graph.fake import FakeGraphProvider
from app.repositories.graph_repository import GraphRepository
from app.services.recommendation.graph_rag import GraphRAGService


class TestGraphRAG(unittest.TestCase):
    def test_fake_graph_provider_queries(self):
        provider = FakeGraphProvider()
        repo = GraphRepository(provider)

        candidates = repo.get_candidates_for_bottleneck("demo-user", "confidence")
        self.assertGreater(len(candidates), 0)
        self.assertEqual(candidates[0]["title"], "Speaking in Public: The Essential Guide")
        self.assertEqual(len(provider.queries_run), 1)
        self.assertIn("MATCH (u:User {id: $userId})", provider.queries_run[0]["cypher"])

    def test_graph_rag_service_context_formatting(self):
        provider = FakeGraphProvider()
        repo = GraphRepository(provider)
        rag_service = GraphRAGService(repo)

        result = rag_service.retrieve_graph_context("demo-user", "confidence")
        self.assertEqual(result["user_id"], "demo-user")
        self.assertEqual(result["bottleneck_type"], "confidence")
        self.assertIn("Speaking in Public", result["formatted_graph_context"])
        self.assertIn("Addresses Markers: Public Speaking", result["formatted_graph_context"])


if __name__ == "__main__":
    unittest.main()
