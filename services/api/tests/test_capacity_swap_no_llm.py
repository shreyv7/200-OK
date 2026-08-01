from __future__ import annotations

from app.services.recommendation.curation_cycle import run_curation_cycle
from app.services.recommendation.variants import generate_variants, select_variant_by_capacity
from tests.fixtures.sample_data import (
    sample_decision_packet_with_bottleneck,
    sample_guardian_context,
)


def test_capacity_swap_returns_micro_variant_from_graph() -> None:
    packet = sample_decision_packet_with_bottleneck()

    result = run_curation_cycle(
        packet,
        run_id="run-capacity-swap",
        persist_active_stack=False,
        guardian_context=sample_guardian_context(capacity_pct=20),
        with_variants=True,
    )

    assert result.stack is not None
    assert len(result.stack.elements) == 1
    assert "60-second" in result.stack.elements[0].title.lower()
    assert result.guardian_decision is not None
    assert result.guardian_decision["intensity"] == "micro"


def test_select_variant_by_capacity_is_local() -> None:
    from tests.fixtures.sample_data import sample_active_stack_for_variants

    variants = generate_variants(sample_active_stack_for_variants())
    selected = select_variant_by_capacity(variants, 20)
    assert selected.intensity == "micro"
