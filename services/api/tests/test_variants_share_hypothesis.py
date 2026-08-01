from __future__ import annotations

from app.services.recommendation.variants import generate_variants
from tests.fixtures.sample_data import sample_active_stack_for_variants


def test_variants_share_hypothesis_id() -> None:
    stack = sample_active_stack_for_variants()
    variants = generate_variants(stack)

    assert len(variants) == 3
    hypothesis_ids = {variant.hypothesisId for variant in variants}
    assert len(hypothesis_ids) == 1
    assert stack.hypothesisId in hypothesis_ids
    intensities = {variant.intensity for variant in variants}
    assert intensities == {"full", "light", "micro"}
    for variant in variants:
        assert len(variant.stack.elements) >= 1
