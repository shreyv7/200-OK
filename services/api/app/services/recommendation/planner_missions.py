"""Micro-mission planner — bottleneck-targeted actions for the Identity Stack."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.bottleneck import BottleneckLabel
from app.services.recommendation.lens_weights import DEFAULT_LENS_WEIGHTS, get_lens_weights

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.45
MEDIA_LENS_DEPRIORITIZED = 0.25

MISSION_TEMPLATES: dict[BottleneckLabel, str] = {
    "execution": "Publish one small artifact today that proves forward motion",
    "confidence": "Share one unpolished clip with a trusted peer",
    "consistency": "Complete one 10-minute practice block before noon",
    "accountability": "Send a progress update to one accountability partner",
    "knowledge": "Teach one concept you learned this week in 3 bullets",
    "communication": "Deliver a 90-second structured update out loud",
    "focus": "Protect one distraction-free block for your top growth action",
    "networking": "Reach out to one person one step ahead on your path",
    "discipline": "Finish the smallest version of today's committed action",
    "burnout": "Take one restorative break, then do the smallest viable rep",
}

_DEFAULT_LABEL: BottleneckLabel = "execution"


def _normalize_bottleneck(bottleneck: str) -> BottleneckLabel:
    if bottleneck in MISSION_TEMPLATES:
        return bottleneck  # type: ignore[return-value]
    return _DEFAULT_LABEL


def _load_lens_weights(user_id: str | None, db: Session | None) -> dict[str, float]:
    weights = deepcopy(DEFAULT_LENS_WEIGHTS)
    if db is not None and user_id:
        try:
            from app.repositories import ledger_repository

            adjustments = ledger_repository.get_lens_weights(db, user_id)
            if adjustments:
                for lens, delta in adjustments.items():
                    base = weights.get(lens, 0.0)
                    weights[lens] = max(0.0, base + delta)
                total = sum(weights.values()) or 1.0
                return {lens: value / total for lens, value in weights.items()}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load ledger lens weights for %s: %s", user_id, exc)
    if user_id:
        weights = get_lens_weights(user_id)
    return weights


def resolve_small_experiment(
    *,
    small_experiment: bool,
    bottleneck_confidence: float | None,
    lens_weights: dict[str, float],
) -> bool:
    """Deterministic planner context — low confidence or post-unlearning micro tone."""
    if small_experiment:
        return True
    if bottleneck_confidence is not None and bottleneck_confidence < LOW_CONFIDENCE_THRESHOLD:
        return True
    media_weight = lens_weights.get("media", DEFAULT_LENS_WEIGHTS["media"])
    mission_weight = lens_weights.get("micro_mission", DEFAULT_LENS_WEIGHTS["micro_mission"])
    return media_weight <= MEDIA_LENS_DEPRIORITIZED and mission_weight >= media_weight


def build_planner_candidates(
    bottleneck: str,
    *,
    small_experiment: bool = False,
    bottleneck_confidence: float | None = None,
    user_id: str | None = None,
    db: Session | None = None,
) -> list[dict[str, Any]]:
    """Emit ≥1 micro_mission candidate; never empty."""
    label = _normalize_bottleneck(bottleneck)
    lens_weights = _load_lens_weights(user_id, db)
    use_small_experiment = resolve_small_experiment(
        small_experiment=small_experiment,
        bottleneck_confidence=bottleneck_confidence,
        lens_weights=lens_weights,
    )

    title = MISSION_TEMPLATES[label]
    if use_small_experiment:
        title = f"Small experiment: {title.lower()}"

    return [
        {
            "id": f"cand-mission-{label}",
            "type": "micro_mission",
            "title": title,
            "sourceBadge": "Curated fallback",
            "metadata": {
                "bottleneck": label,
                "smallExperiment": use_small_experiment,
                "lensWeights": lens_weights,
            },
        }
    ]
