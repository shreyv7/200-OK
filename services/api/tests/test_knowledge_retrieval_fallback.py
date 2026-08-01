from __future__ import annotations

from app.providers.search.fake import FakeSearchProvider
from app.services.recommendation.curation_cycle import run_curation_cycle
from tests.fixtures.sample_data import sample_decision_packet


class RaisingSearchProvider(FakeSearchProvider):
    def search(self, query: str, opts=None):  # type: ignore[no-untyped-def]
        raise TimeoutError("search timeout")


def test_knowledge_retrieval_fallback_never_empty() -> None:
    packet = sample_decision_packet()
    stack = run_curation_cycle(
        packet,
        run_id="run-m4-fallback",
        search=RaisingSearchProvider(),
        persist_active_stack=False,
    )

    assert len(stack.elements) >= 2
    assert any(e.sourceBadge == "Curated fallback" for e in stack.elements)


def test_empty_search_results_use_fallback_catalog() -> None:
    packet = sample_decision_packet()
    stack = run_curation_cycle(
        packet,
        run_id="run-m4-empty-search",
        search=FakeSearchProvider(documents=[]),
        persist_active_stack=False,
    )

    assert len(stack.elements) >= 2
