from __future__ import annotations

from app.services.recommendation.lens_weights import apply_unlearning


def test_media_lens_unlearning_reduces_weight_by_40_percent() -> None:
    weights = {"media": 0.5, "knowledge": 0.25, "micro_mission": 0.25}
    updated, adjustment = apply_unlearning(weights, failed_lens="media")

    assert updated["media"] < weights["media"]
    assert adjustment["media"] < 0
    assert abs(sum(updated.values()) - 1.0) < 1e-6
