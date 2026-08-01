"""Lattice Strut Contributor query module for AIA.

Provides detailed contributing evidence events for F3 lattice strut click popovers.
Calculates timestamp, base weight, decay factor, and decayed contribution per event.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from app.schemas.evidence import EvidenceEvent
from app.schemas.identity import IdentityAttribute
from app.services.identity.sanitizer import get_event_delta_days
from app.services.identity.scoring.gap import (
    decay_weight,
    compute_deficit,
    compute_revealed,
    EvidenceInput,
)


@dataclass
class StrutContributor:
    eventId: str
    type: str
    timestamp: datetime
    deltaDays: float
    baseWeight: float
    value: float
    decayFactor: float
    decayedContribution: float
    source: str
    simulated: bool


@dataclass
class LatticeStrutDetail:
    attrId: str
    attrLabel: str
    weight: float
    targetWeeklyPoints: float
    revealedPoints: float
    deficit: float
    creationContribution: float
    passiveContribution: float
    driftContribution: float
    contributingEvents: List[StrutContributor] = field(default_factory=list)


def get_lattice_strut_detail(
    attr: IdentityAttribute,
    events: List[EvidenceEvent],
    window_days: int = 21,
    ref_time: Optional[datetime] = None,
    limit: int = 10,
) -> LatticeStrutDetail:
    """Returns detailed lattice strut breakdown and top contributing evidence events for attr."""
    if ref_time is None:
        ref_time = datetime.now(timezone.utc)

    contributors: List[StrutContributor] = []
    evidence_inputs: List[EvidenceInput] = []

    for e in events:
        delta = get_event_delta_days(e.timestamp, ref_time)
        if delta <= window_days and attr.id in e.identityAttributeIds:
            decay_f = decay_weight(delta)
            decayed_c = e.value * decay_f
            
            contributors.append(
                StrutContributor(
                    eventId=e.id,
                    type=e.type,
                    timestamp=e.timestamp,
                    deltaDays=round(delta, 2),
                    baseWeight=e.baseWeight,
                    value=e.value,
                    decayFactor=round(decay_f, 4),
                    decayedContribution=round(decayed_c, 2),
                    source=e.source,
                    simulated=e.simulated,
                )
            )

            evidence_inputs.append(
                EvidenceInput(
                    event_type=e.type,
                    attr_id=attr.id,
                    a_ik=1.0,
                    delta_days=delta,
                    value_override=e.value,
                )
            )

    # Sort contributors descending by decayed contribution (highest impact first)
    contributors.sort(key=lambda x: x.decayedContribution, reverse=True)
    top_contributors = contributors[:limit]

    R_i, creation_c, passive_c, drift_c = compute_revealed(evidence_inputs, attr.id)
    deficit_i = compute_deficit(attr.targetWeeklyPoints, R_i)

    return LatticeStrutDetail(
        attrId=attr.id,
        attrLabel=attr.label,
        weight=attr.weight,
        targetWeeklyPoints=attr.targetWeeklyPoints,
        revealedPoints=round(R_i, 2),
        deficit=round(deficit_i, 4),
        creationContribution=round(creation_c, 2),
        passiveContribution=round(passive_c, 2),
        driftContribution=round(drift_c, 2),
        contributingEvents=top_contributors,
    )
