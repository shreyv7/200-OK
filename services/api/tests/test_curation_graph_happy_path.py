from __future__ import annotations

from app.providers.search.base import Document
from app.providers.search.fake import FakeSearchProvider
from app.services.recommendation.curation_cycle import run_curation_cycle
from tests.fixtures.sample_data import sample_decision_packet


def test_curation_graph_happy_path_live_badge() -> None:
    live_docs = [
        Document(
            title="Live article on shipping",
            url="https://example.com/live",
            extract="Ship small.",
            source="live_web",
        )
    ]
    search = FakeSearchProvider(documents=live_docs)
    packet = sample_decision_packet()

    stack = run_curation_cycle(
        packet,
        run_id="run-m4-happy",
        search=search,
        persist_active_stack=False,
    )

    assert len(stack.elements) >= 2
    assert any(e.type == "micro_mission" for e in stack.elements)
    assert any(e.type in {"media", "knowledge"} for e in stack.elements)
    assert any(e.sourceBadge in {"Live web", "Cached web"} for e in stack.elements)
    assert all(
        e.explanation.whyThis and e.explanation.whyNow and e.explanation.howReducesGap
        for e in stack.elements
    )
    assert len(stack.elements) <= 4
