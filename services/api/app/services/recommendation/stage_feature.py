"""Decode journey stage from DecisionPacket.rankingFeatures — AIS M6."""

from __future__ import annotations

STAGE_FEATURE_KEY = "stageIndex"
STAGES = ("early", "mid", "late")
DEFAULT_STAGE = "early"


def stage_from_ranking_features(features: dict[str, float]) -> str:
    """Read stage from numeric ranking features until AIA adds a typed field."""
    if STAGE_FEATURE_KEY in features:
        index = int(features[STAGE_FEATURE_KEY])
        if 0 <= index < len(STAGES):
            return STAGES[index]
    return DEFAULT_STAGE


def ranking_features_for_stage(stage: str) -> dict[str, float]:
    """Encode stage for DecisionPacket.rankingFeatures contract tests."""
    try:
        index = STAGES.index(stage)
    except ValueError:
        index = 0
    return {STAGE_FEATURE_KEY: float(index)}
