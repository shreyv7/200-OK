"""Pure Python deterministic Gap scoring arithmetic functions.

PRD §9 Source of Truth — No LLM math, no database dependencies.
"""

from dataclasses import dataclass
import math
from typing import List, Tuple

from app.services.identity.scoring.constants import (
    LAMBDA,
    EVENT_WEIGHTS,
    CREATION_TYPES,
    PASSIVE_TYPES,
    DRIFT_TYPES,
)


@dataclass
class EvidenceInput:
    event_type: str
    attr_id: str
    a_ik: float  # Applicability score in [0, 1]
    delta_days: float  # Age of event in days (>= 0)
    value_override: float | None = None


@dataclass
class AttrInput:
    attr_id: str
    w_i: float  # Weight in [0, 1], sum(w_i) == 1.0
    D_i: float  # Declared target in evidence points (> 0)


@dataclass
class AttributeBreakdown:
    attr_id: str
    w_i: float
    D_i: float
    R_i: float
    deficit: float
    creation_contribution: float
    passive_contribution: float
    drift_contribution: float


@dataclass
class GapResult:
    gap_score: int
    alignment: int
    per_attribute: List[AttributeBreakdown]


@dataclass
class CreateConsumeResult:
    create_points: float
    consume_points: float
    drift_points: float
    ratio: float


def decay_weight(delta_days: float) -> float:
    """Calculates seven-day half-life exponential decay factor e^(-lambda * delta_days)."""
    if delta_days < 0:
        delta_days = 0.0
    return math.exp(-LAMBDA * delta_days)


def compute_revealed(events: List[EvidenceInput], attr_id: str) -> Tuple[float, float, float, float]:
    """Computes R_i (Revealed evidence total) and contribution breakdowns for attribute attr_id.
    
    Returns (R_i, creation_contribution, passive_contribution, drift_contribution).
    """
    R_i = 0.0
    creation_contrib = 0.0
    passive_contrib = 0.0
    drift_contrib = 0.0

    for e in events:
        if e.attr_id != attr_id:
            continue
        
        base_w = e.value_override if e.value_override is not None else EVENT_WEIGHTS.get(e.event_type, 1.0)
        decay = decay_weight(e.delta_days)
        contribution = e.a_ik * base_w * decay
        R_i += contribution

        if e.event_type in CREATION_TYPES:
            creation_contrib += contribution
        elif e.event_type in PASSIVE_TYPES:
            passive_contrib += contribution
        elif e.event_type in DRIFT_TYPES:
            drift_contrib += abs(contribution)

    return R_i, creation_contrib, passive_contrib, drift_contrib


def compute_deficit(D_i: float, R_i: float) -> float:
    """Computes normalized deficit_i = clamp((D_i - R_i) / D_i, 0.0, 1.0)."""
    if D_i <= 0:
        return 0.0
    raw_deficit = (D_i - R_i) / D_i
    return max(0.0, min(1.0, raw_deficit))


def compute_gap_score(attributes: List[AttrInput], events: List[EvidenceInput]) -> GapResult:
    """Computes deterministic Identity Gap score (0-100) and per-attribute breakdown."""
    if not attributes:
        return GapResult(gap_score=0, alignment=100, per_attribute=[])

    weighted_deficits = 0.0
    breakdowns: List[AttributeBreakdown] = []

    for attr in attributes:
        R_i, creation_c, passive_c, drift_c = compute_revealed(events, attr.attr_id)
        def_i = compute_deficit(attr.D_i, R_i)
        weighted_deficits += attr.w_i * def_i

        breakdowns.append(
            AttributeBreakdown(
                attr_id=attr.attr_id,
                w_i=attr.w_i,
                D_i=attr.D_i,
                R_i=R_i,
                deficit=def_i,
                creation_contribution=creation_c,
                passive_contribution=passive_c,
                drift_contribution=drift_c,
            )
        )

    gap_score = round(100.0 * weighted_deficits)
    gap_score = max(0, min(100, gap_score))
    alignment = 100 - gap_score

    return GapResult(
        gap_score=gap_score,
        alignment=alignment,
        per_attribute=breakdowns,
    )


def compute_create_consume(events: List[EvidenceInput]) -> CreateConsumeResult:
    """Computes Create:Consume ratio = CreatePoints / max(1, ConsumePoints + DriftPoints)."""
    create_pts = 0.0
    consume_pts = 0.0
    drift_pts = 0.0

    for e in events:
        base_w = e.value_override if e.value_override is not None else EVENT_WEIGHTS.get(e.event_type, 1.0)
        decay = decay_weight(e.delta_days)
        contrib = e.a_ik * base_w * decay

        if e.event_type in CREATION_TYPES and contrib > 0:
            create_pts += contrib
        elif e.event_type in PASSIVE_TYPES and contrib > 0:
            consume_pts += contrib
        elif e.event_type in DRIFT_TYPES:
            drift_pts += abs(contrib)

    denom = max(1.0, consume_pts + drift_pts)
    ratio = round(create_pts / denom, 2)

    return CreateConsumeResult(
        create_points=round(create_pts, 2),
        consume_points=round(consume_pts, 2),
        drift_points=round(drift_pts, 2),
        ratio=ratio,
    )


def compute_consistency(events: List[EvidenceInput], window_days: int = 7) -> float:
    """Computes fraction of days in window [0, window_days] with positive evidence."""
    if window_days <= 0:
        return 0.0

    active_days: set[int] = set()
    for e in events:
        if 0 <= e.delta_days <= window_days and e.event_type not in DRIFT_TYPES:
            active_days.add(math.floor(e.delta_days))

    return round(len(active_days) / float(window_days), 2)


def compute_momentum(gap_now: int, gap_7d_ago: int) -> int:
    """Computes 7-day signed gap delta (gap_now - gap_7d_ago). Negative = improvement."""
    return gap_now - gap_7d_ago
