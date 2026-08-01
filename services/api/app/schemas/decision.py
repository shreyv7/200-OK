"""Decision packet — owned by AIA Growth Decision Engine; consumed by AIS Coordinator."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.bottleneck import BottleneckPacket


class DecisionPacket(BaseModel):
    userId: str
    gapDelta: float
    invalidateStack: bool = False
    invalidatedElementIds: list[str] = Field(default_factory=list)
    bottleneck: BottleneckPacket | None = None
    rankingFeatures: dict[str, float] = Field(default_factory=dict)
