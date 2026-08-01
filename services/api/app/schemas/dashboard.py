"""Dashboard summary contract. Owner: Backend. F3 (prd.md), milestones.md M2."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.bottleneck import BottleneckPacket
from app.schemas.gap import GapBreakdown
from app.schemas.identity import DeclaredSelf


class DashboardSummary(BaseModel):
    userId: str
    declaredSelf: DeclaredSelf
    gap: GapBreakdown
    bottleneck: BottleneckPacket | None = None
    capacity: float
