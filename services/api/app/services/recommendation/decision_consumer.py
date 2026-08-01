"""Growth Decision Engine consumer — AIS M2.

Reads precomputed Gap/KPI snapshots from Backend/AIA and produces schema
DecisionPackets plus active-stack invalidation flags.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas import DecisionPacket, IdentityStack
from app.services.decision.packet import build_decision_packet
from app.services.identity.scoring.gap import GapResult
from app.services.recommendation.decision_adapter import from_gap_snapshot, to_schema_decision_packet
from app.services.recommendation.gap_snapshot import GapSnapshot
from app.services.recommendation.stack_state import ActiveStackFlags, apply_invalidation, get_active_stack


@dataclass
class ConsumeResult:
    packet: DecisionPacket
    flags: ActiveStackFlags


def _prior_gap_from_snapshot(snapshot: GapSnapshot) -> int | None:
    if snapshot.priorGapScore is not None:
        return snapshot.priorGapScore
    return int(round(snapshot.gapScore - snapshot.gapDelta))


def consume_gap_update(
    snapshot: GapSnapshot,
    *,
    active_stack: IdentityStack | None = None,
) -> ConsumeResult:
    """Consume a GapSnapshot and apply invalidation flags (empty stack allowed)."""
    if active_stack is None:
        active_stack = get_active_stack(snapshot.userId)

    gap_result = GapResult(
        gap_score=snapshot.gapScore,
        alignment=snapshot.alignment,
        per_attribute=[],
    )
    aia_packet = build_decision_packet(
        user_id=snapshot.userId,
        gap_result=gap_result,
        prior_gap_score=_prior_gap_from_snapshot(snapshot),
        create_consume_ratio=snapshot.createConsumeRatio,
        timestamp=snapshot.timestamp,
    )

    invalidated_ids: list[str] = []
    if aia_packet.invalidate_stack and active_stack is not None:
        invalidated_ids = [element.id for element in active_stack.elements]

    schema_packet = from_gap_snapshot(
        snapshot,
        invalidate_stack=aia_packet.invalidate_stack,
        invalidated_element_ids=invalidated_ids,
    )
    schema_packet = schema_packet.model_copy(
        update={
            "rankingFeatures": to_schema_decision_packet(
                aia_packet,
                consistency=snapshot.consistency,
                momentum=snapshot.momentum,
            ).rankingFeatures,
        }
    )

    flags = apply_invalidation(snapshot.userId, schema_packet)
    return ConsumeResult(packet=schema_packet, flags=flags)
