"""Digital Twin Read Model module for AIA.

Combines active confirmed DeclaredSelf with current RevealedSelfAggregates and GapResult.
"""

from dataclasses import dataclass
from typing import List, Optional

from app.services.identity.scoring.declared_self import DeclaredSelf
from app.services.identity.scoring.gap import (
    AttrInput,
    EvidenceInput,
    GapResult,
    compute_gap_score,
)
from app.services.identity.sanitizer import SanitizedEvent
from app.services.identity.aggregates import (
    RevealedSelfAggregates,
    build_revealed_aggregates,
)


@dataclass
class DigitalTwinReadModel:
    user_id: str
    declared_version: int
    declared_self: DeclaredSelf
    revealed_aggregates: RevealedSelfAggregates
    gap_result: GapResult
    last_updated_at: str


def assemble_digital_twin(
    user_id: str,
    declared_self: DeclaredSelf,
    events: List[SanitizedEvent],
    window_days: int = 21,
    timestamp: str = "2026-08-01T12:00:00Z",
) -> DigitalTwinReadModel:
    """Assembles unified Digital Twin read model combining DeclaredSelf, RevealedAggregates, and GapResult."""
    attr_ids = [attr["id"] for attr in declared_self.get("attributes", [])]
    attr_inputs = [
        AttrInput(
            attr_id=attr["id"],
            w_i=attr["weight"],
            D_i=attr["declared_weekly_target"],
        )
        for attr in declared_self.get("attributes", [])
    ]

    # Filter events inside temporal window
    window_events = [e for e in events if e.delta_days <= window_days]

    # Build revealed aggregates
    revealed = build_revealed_aggregates(window_events, attr_ids, window_days=window_days)

    # Convert to EvidenceInput list for Gap calculation
    evidence_inputs = [
        EvidenceInput(
            event_type=e.event_type,
            attr_id=e.attr_id,
            a_ik=e.a_ik,
            delta_days=e.delta_days,
            value_override=e.value_override,
        )
        for e in window_events
    ]

    # Compute GapResult
    gap_res = compute_gap_score(attr_inputs, evidence_inputs)

    return DigitalTwinReadModel(
        user_id=user_id,
        declared_version=declared_self.get("version", 1),
        declared_self=declared_self,
        revealed_aggregates=revealed,
        gap_result=gap_res,
        last_updated_at=timestamp,
    )
