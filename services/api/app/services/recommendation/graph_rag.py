"""Graph & Text RAG Recommendation Service. Owner: AIS.

Combines Cypher graph traversal paths with full-text search results
and formats multi-hop graph facts for the Curator LLM context.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.repositories.graph_repository import GraphRepository


class GraphRAGService:
    def __init__(self, repo: GraphRepository) -> None:
        self.repo = repo

    def retrieve_graph_context(
        self, user_id: str, bottleneck_type: str, search_query: str | None = None
    ) -> Dict[str, Any]:
        """Runs multi-hop Cypher retrieval + optional text search and formats RAG context payload."""

        # 1. Multi-hop Graph Cypher Retrieval
        graph_candidates = self.repo.get_candidates_for_bottleneck(
            user_id=user_id, bottleneck_type=bottleneck_type, limit=10
        )

        # 2. Text Search RAG if search query provided
        text_candidates = []
        if search_query:
            try:
                text_candidates = self.repo.fulltext_search_resources(search_query=search_query, limit=5)
            except Exception:
                # Gracefully fall back if full-text index is uninitialized or in fake mode
                text_candidates = []

        # 3. Format Graph Paths into Text Facts for LLM Prompt Context
        context_facts: List[str] = []
        for candidate in graph_candidates:
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
            "graph_candidates": graph_candidates,
            "text_candidates": text_candidates,
            "formatted_graph_context": formatted_context,
        }


def graph_candidates_as_knowledge(
    user_id: str,
    bottleneck: str,
    *,
    provider: Any | None = None,
    limit: int = 2,
) -> list[dict[str, Any]]:
    """Format graph RAG hits as Knowledge lens candidate dicts."""
    from app.providers.graph.fake import FakeGraphProvider

    graph_provider = provider or FakeGraphProvider()
    repo = GraphRepository(graph_provider)
    service = GraphRAGService(repo)
    context = service.retrieve_graph_context(user_id, bottleneck)
    candidates: list[dict[str, Any]] = []
    for index, hit in enumerate(context["graph_candidates"][:limit]):
        candidates.append(
            {
                "id": f"cand-graph-{index}",
                "type": "knowledge",
                "title": hit.get("title") or "Graph growth resource",
                "url": hit.get("url"),
                "sourceBadge": "Graph RAG",
                "extract": hit.get("extract") or "",
                "metadata": {"bottleneck": bottleneck},
            }
        )
    return candidates


def get_graph_rag_service(provider: Any | None = None) -> GraphRAGService:
    """Factory for Graph RAG service with configured provider."""
    from app.providers.graph.fake import FakeGraphProvider
    from app.repositories.graph_repository import GraphRepository

    graph_provider = provider or FakeGraphProvider()
    return GraphRAGService(GraphRepository(graph_provider))
