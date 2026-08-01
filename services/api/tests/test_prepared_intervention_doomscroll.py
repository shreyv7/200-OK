from __future__ import annotations

from app.providers.llm.fake import FakeLLMProvider
from app.providers.search.fake import FakeSearchProvider
from app.services.recommendation.prepared_intervention import prepare_doomscroll_intervention
from app.services.recommendation.stack_state import clear_stack_state
from tests.fixtures.sample_data import sample_decision_packet_with_bottleneck


def test_prepare_doomscroll_intervention_returns_stack_variants_and_alternate() -> None:
    clear_stack_state()
    llm = FakeLLMProvider()
    search = FakeSearchProvider()

    prepared = prepare_doomscroll_intervention(
        "user-aarav",
        decision_packet=sample_decision_packet_with_bottleneck(bottleneck="execution"),
        run_id="prep-test",
        llm=llm,
        search=search,
    )

    assert len(prepared.stack.elements) >= 2
    assert {variant.intensity for variant in prepared.variants} == {"full", "light", "micro"}
    assert prepared.alternate_stack.elements
    assert prepared.alternate_stack.elements[0].type == "micro_mission"
    assert prepared.variants_payload()["micro"]["hypothesisId"] == prepared.stack.hypothesisId
