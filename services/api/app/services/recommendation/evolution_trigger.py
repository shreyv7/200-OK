"""Evolution accept event — AIS consume seam (promote to app.schemas if Backend asks)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.services.recommendation.gap_snapshot import GapSnapshot


@dataclass(frozen=True)
class EvolutionAcceptedEvent:
    userId: str
    declaredSelfVersion: int
    acceptedAt: str
    gapSnapshot: GapSnapshot | None = None
    trigger: Literal["evolution.accepted"] = "evolution.accepted"
