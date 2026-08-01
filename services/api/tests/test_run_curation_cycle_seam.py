from __future__ import annotations

from app.schemas import IdentityStack
from app.services.recommendation.curation_cycle import run_curation_cycle
from tests.fixtures.sample_data import sample_decision_packet_with_bottleneck


def test_run_curation_cycle_returns_schema_valid_stack() -> None:
    packet = sample_decision_packet_with_bottleneck()
    stack = run_curation_cycle(packet, run_id="run-seam", persist_active_stack=False)

    validated = IdentityStack.model_validate(stack.model_dump())
    assert validated.userId == packet.userId
    assert len(validated.elements) >= 2
