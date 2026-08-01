"""Revealed Self Aggregate Builder module for AIA.

Computes aggregated behavioral points, event counts, and ratios over rolling temporal windows.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.services.identity.sanitizer import SanitizedEvent
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
    events: List[SanitizedEvent],
    attribute_ids: List[str],
    window_days: int = 21,
) -> RevealedSelfAggregates:
    """Builds RevealedSelfAggregates over a rolling time window (default 21 days).
    
    Serves as input to Gap computation and Twin read model.
    """
    # Filter events inside the temporal window
    window_events = [e for e in events if e.delta_days <= window_days]
    
    # Convert SanitizedEvent list to EvidenceInput list for gap arithmetic helpers
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

    attr_aggs: Dict[str, AttributeAggregate] = {}

    for attr_id in attribute_ids:
        R_i, creation_c, passive_c, drift_c = compute_revealed(evidence_inputs, attr_id)
        
        attr_events = [e for e in window_events if e.attr_id == attr_id]
        event_count = len(attr_events)
        last_delta = min((e.delta_days for e in attr_events), default=None)

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
