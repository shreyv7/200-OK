"""Consume AIA bottleneck packet from DecisionPacket — AIS M4."""

from __future__ import annotations

import logging
from typing import Any

from app.schemas import BottleneckPacket, DecisionPacket

logger = logging.getLogger(__name__)

SMALL_EXPERIMENT_THRESHOLD = 0.45
DEFAULT_BOTTLENECK = "execution"


def consume_bottleneck_diagnosis(packet: DecisionPacket | dict[str, Any]) -> dict[str, Any]:
    """Normalize bottleneck from DecisionPacket; AIS never re-diagnoses."""
    if isinstance(packet, dict):
        packet = DecisionPacket.model_validate(packet)

    bottleneck_data = packet.bottleneck
    if bottleneck_data is None:
        logger.warning(
            "DecisionPacket missing bottleneck for user %s — using degraded default",
            packet.userId,
        )
        bottleneck_data = BottleneckPacket(
            bottleneck=DEFAULT_BOTTLENECK,
            confidence=0.5,
            supporting_evidence=[],
            missing_evidence=["bottleneck_packet"],
            alternative_bottleneck=None,
        )

    bottleneck_packet = (
        bottleneck_data
        if isinstance(bottleneck_data, BottleneckPacket)
        else BottleneckPacket.model_validate(bottleneck_data)
    )
    small_experiment = bottleneck_packet.confidence < SMALL_EXPERIMENT_THRESHOLD

    return {
        "bottleneck_packet": bottleneck_packet.model_dump(),
        "small_experiment": small_experiment,
    }
