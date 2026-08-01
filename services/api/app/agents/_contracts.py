"""TEMP MIRROR — replace with app.schemas on Backend M0 merge."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

CONTRACT_SOURCE = "mirror"


class ElementType(str, Enum):
    MEDIA = "media"
    KNOWLEDGE = "knowledge"
    GROWTH_STORY = "growth_story"
    MENTOR = "mentor"
    TOOL = "tool"
    EXPERIENCE = "experience"
    MICRO_MISSION = "micro_mission"
    REFLECTION = "reflection"


class SourceBadge(str, Enum):
    LIVE_WEB = "live_web"
    CACHED_WEB = "cached_web"
    CURATED_FALLBACK = "curated_fallback"
    SIMULATED = "simulated"


class IdentityStackElement(BaseModel):
    element_id: str
    element_type: ElementType
    title: str
    url: str | None = None
    hypothesis_id: str
    source_badge: SourceBadge
    why_this: str
    why_now: str
    how_reduces_gap: str
    simulated: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class IdentityStack(BaseModel):
    stack_id: str
    hypothesis_id: str
    curated_at: datetime
    elements: list[IdentityStackElement]
    invalidate: bool = False
    simulated: bool = False


class BottleneckPacket(BaseModel):
    bottleneck: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    alternative_bottleneck: str | None = None


class DecisionPacket(BaseModel):
    run_id: str
    user_id: str
    gap_score: float | None = None
    gap_delta: float | None = None
    invalidate_stack: bool = False
    bottleneck: BottleneckPacket | None = None
    trigger: str = "manual"
    metadata: dict[str, Any] = Field(default_factory=dict)


class LedgerEntry(BaseModel):
    entry_id: str
    hypothesis_id: str
    hypothesis_family: str
    verdict: str = "pending"
    lens: str
    dismissals: int = 0
    unlearning_applied: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class InterventionVariant(str, Enum):
    FULL = "full"
    LIGHT = "light"
    MICRO = "micro"


class InterventionVariantSet(BaseModel):
    hypothesis_id: str
    full: IdentityStack
    light: IdentityStack
    micro: IdentityStack
