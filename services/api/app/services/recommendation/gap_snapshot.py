"""GapSnapshot — precomputed Gap/KPI inputs passed by Backend after AIA recompute.

AIS is a pure consumer: it never derives Gap from raw evidence events.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GapSnapshot:
    userId: str
    gapScore: int
    gapDelta: float
    alignment: int
    createConsumeRatio: float
    consistency: float = 0.0
    momentum: float = 0.0
    timestamp: str = ""
    priorGapScore: int | None = None
