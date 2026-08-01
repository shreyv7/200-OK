"""Run-scoped Coordinator context — AIS-owned, not persisted in Backend DecisionPacket."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TriggerType = Literal["evidence.created", "manual"]


@dataclass
class CoordinatorRunContext:
    run_id: str
    trigger: TriggerType
    gap_score: float | None = None
