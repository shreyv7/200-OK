"""Deterministic lens-weight adaptation — AIS M5."""

from __future__ import annotations

from copy import deepcopy

from app.services.recommendation.guardian_constants import MEDIA_LENS_UNLEARNING_FACTOR

DEFAULT_LENS_WEIGHTS: dict[str, float] = {
    "media": 0.4,
    "knowledge": 0.2,
    "micro_mission": 0.4,
}

_user_lens_weights: dict[str, dict[str, float]] = {}


def clear_lens_weights() -> None:
    """Test helper."""
    _user_lens_weights.clear()


def get_lens_weights(user_id: str) -> dict[str, float]:
    stored = _user_lens_weights.get(user_id)
    if stored is None:
        return deepcopy(DEFAULT_LENS_WEIGHTS)
    return deepcopy(stored)


def set_lens_weights(user_id: str, weights: dict[str, float]) -> None:
    _user_lens_weights[user_id] = deepcopy(weights)


def apply_unlearning(
    weights: dict[str, float],
    *,
    failed_lens: str = "media",
) -> tuple[dict[str, float], dict[str, float]]:
    """Apply −40% relative reduction to failed lens and renormalize."""
    updated = deepcopy(weights)
    if failed_lens not in updated:
        updated[failed_lens] = DEFAULT_LENS_WEIGHTS.get(failed_lens, 0.1)

    prior = updated[failed_lens]
    updated[failed_lens] = max(0.0, prior * (1.0 - MEDIA_LENS_UNLEARNING_FACTOR))

    total = sum(updated.values()) or 1.0
    normalized = {lens: value / total for lens, value in updated.items()}
    adjustment = {failed_lens: normalized[failed_lens] - prior}
    return normalized, adjustment
