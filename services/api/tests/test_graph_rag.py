from __future__ import annotations

from app.providers.graph.fake import FakeGraphProvider
from app.repositories.graph_repository import GraphRepository
from app.services.recommendation.graph_rag import (
    GraphRAGService,
    graph_candidates_as_knowledge,
)


def test_fake_graph_rag_returns_seeded_context() -> None:
    provider = FakeGraphProvider()
    service = GraphRAGService(GraphRepository(provider))
    context = service.retrieve_graph_context("user-1", "confidence")

    assert context["user_id"] == "user-1"
    assert context["bottleneck_type"] == "confidence"
    assert context["graph_candidates"]
    assert "Candidate" in context["formatted_graph_context"]
    assert provider.queries_run


def test_graph_candidates_shape_for_knowledge_node() -> None:
    candidates = graph_candidates_as_knowledge(
        "user-1", "confidence", provider=FakeGraphProvider(), limit=2
    )
    assert candidates
    assert candidates[0]["sourceBadge"] == "Graph RAG"
    assert candidates[0]["title"]
