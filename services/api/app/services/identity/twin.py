"""Digital Twin Read Model module for AIA.

Combines Backend DeclaredSelf Pydantic model with RevealedSelfAggregates and GapResult.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from app.schemas.identity import DeclaredSelf
from app.schemas.evidence import EvidenceEvent
from app.services.identity.sanitizer import get_event_delta_days
from app.services.identity.scoring.gap import (
    AttrInput,
    EvidenceInput,
    GapResult,
    compute_gap_score,
)
from app.services.identity.aggregates import (
    RevealedSelfAggregates,
    build_revealed_aggregates,
)


@dataclass
class DigitalTwinReadModel:
    userId: str
    declaredVersion: int
    declaredSelf: DeclaredSelf
    revealedAggregates: RevealedSelfAggregates
    gapResult: GapResult
    lastUpdatedAt: datetime


def assemble_digital_twin(
    user_id: str,
    declared_self: DeclaredSelf,
    events: List[EvidenceEvent],
    window_days: int = 21,
    ref_time: Optional[datetime] = None,
) -> DigitalTwinReadModel:
    """Assembles DigitalTwinReadModel combining Backend DeclaredSelf, RevealedAggregates, and GapResult."""
    if ref_time is None:
        ref_time = datetime.now(timezone.utc)

    attr_ids = [attr.id for attr in declared_self.attributes]
    attr_inputs = [
        AttrInput(
            attr_id=attr.id,
            w_i=attr.weight,
            D_i=attr.targetWeeklyPoints,
        )
        for attr in declared_self.attributes
    ]

    # Build revealed aggregates
    revealed = build_revealed_aggregates(events, attr_ids, window_days=window_days, ref_time=ref_time)

    # Convert events to EvidenceInput list for Gap calculation
    evidence_inputs: List[EvidenceInput] = []
    for e in events:
        delta = get_event_delta_days(e.timestamp, ref_time)
        if delta <= window_days:
            for attr_id in e.identityAttributeIds:
                evidence_inputs.append(
                    EvidenceInput(
                        event_type=e.type,
                        attr_id=attr_id,
                        a_ik=1.0,
                        delta_days=delta,
                        value_override=e.value,
                    )
                )

    gap_res = compute_gap_score(attr_inputs, evidence_inputs)

    return DigitalTwinReadModel(
        userId=user_id,
        declaredVersion=declared_self.version,
        declaredSelf=declared_self,
        revealedAggregates=revealed,
        gapResult=gap_res,
        lastUpdatedAt=ref_time,
    )
