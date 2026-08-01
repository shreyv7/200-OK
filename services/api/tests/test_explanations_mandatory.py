from __future__ import annotations

from app.services.recommendation.curation_cycle import run_curation_cycle
from tests.fixtures.sample_data import sample_decision_packet_with_bottleneck


def test_explanations_mandatory_on_every_element() -> None:
    packet = sample_decision_packet_with_bottleneck()
    stack = run_curation_cycle(
        packet,
        run_id="run-explanations",
        persist_active_stack=False,
    )

    for element in stack.elements:
        assert element.explanation.whyThis.strip()
        assert element.explanation.whyNow.strip()
        assert element.explanation.howReducesGap.strip()
