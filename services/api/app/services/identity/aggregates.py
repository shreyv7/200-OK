"""Revealed Self Aggregate Builder module for AIA.

Computes aggregated behavioral points, event counts, and ratios over rolling temporal windows
from Backend EvidenceEvent streams.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from app.schemas.evidence import EvidenceEvent
from app.services.identity.sanitizer import get_event_delta_days
from app.services.identity.scoring.gap import (
    EvidenceInput,
    compute_revealed,
    compute_create_consume,
    compute_consistency,
)


@dataclass
class AttributeAggregate:
    attr_id: str
    total_decayed_points: float
    creation_points: float
    passive_points: float
    drift_points: float
    event_count: int
    last_event_delta_days: Optional[float] = None


@dataclass
class RevealedSelfAggregates:
    window_days: int
    attribute_aggregates: Dict[str, AttributeAggregate] = field(default_factory=dict)
    total_events: int = 0
    create_consume_ratio: float = 0.0
    consistency_score: float = 0.0


def build_revealed_aggregates(
    events: List[EvidenceEvent],
    attribute_ids: List[str],
    window_days: int = 21,
    ref_time: Optional[datetime] = None,
) -> RevealedSelfAggregates:
    """Builds RevealedSelfAggregates from Backend EvidenceEvent stream over a rolling window."""
    evidence_inputs: List[EvidenceInput] = []
    window_events: List[EvidenceEvent] = []

    for e in events:
        delta = get_event_delta_days(e.timestamp, ref_time)
        if delta <= window_days:
            window_events.append(e)
            # Add EvidenceInput for each mapped attribute
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

    attr_aggs: Dict[str, AttributeAggregate] = {}

    for attr_id in attribute_ids:
        R_i, creation_c, passive_c, drift_c = compute_revealed(evidence_inputs, attr_id)
        
        attr_evts = [e for e in window_events if attr_id in e.identityAttributeIds]
        event_count = len(attr_evts)
        last_delta = min((get_event_delta_days(e.timestamp, ref_time) for e in attr_evts), default=None)

        attr_aggs[attr_id] = AttributeAggregate(
            attr_id=attr_id,
            total_decayed_points=round(R_i, 2),
            creation_points=round(creation_c, 2),
            passive_points=round(passive_c, 2),
            drift_points=round(drift_c, 2),
            event_count=event_count,
            last_event_delta_days=round(last_delta, 2) if last_delta is not None else None,
        )

    cc_result = compute_create_consume(evidence_inputs)
    consistency = compute_consistency(evidence_inputs, window_days=min(window_days, 7))

    return RevealedSelfAggregates(
        window_days=window_days,
        attribute_aggregates=attr_aggs,
        total_events=len(window_events),
        create_consume_ratio=cc_result.ratio,
        consistency_score=consistency,
    )
