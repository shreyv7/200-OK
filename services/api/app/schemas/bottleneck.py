"""Bottleneck packet — owned by AIA (prd.md §9); consumed by AIS Curator."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BottleneckLabel = Literal[
    "confidence",
    "consistency",
    "execution",
    "accountability",
    "knowledge",
    "communication",
    "focus",
    "networking",
    "discipline",
    "burnout",
]


class BottleneckPacket(BaseModel):
    bottleneck: BottleneckLabel
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    alternative_bottleneck: BottleneckLabel | None = None
