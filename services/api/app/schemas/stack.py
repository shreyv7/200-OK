"""Identity Stack DTO + Intervention variants — owned by AIS; persisted/served by Backend."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ResourceType = Literal[
    "media",
    "knowledge",
    "growth_story",
    "tool",
    "mentor",
    "real_world_experience",
    "micro_mission",
    "reflection",
]

SourceBadge = Literal["Live web", "Cached web", "Curated fallback"]
VariantIntensity = Literal["full", "light", "micro"]


class StackExplanation(BaseModel):
    whyThis: str
    whyNow: str
    howReducesGap: str


class StackElement(BaseModel):
    id: str
    type: ResourceType
    title: str
    url: str | None = None
    sourceBadge: SourceBadge
    explanation: StackExplanation


class IdentityStack(BaseModel):
    id: str
    userId: str
    hypothesisId: str
    bottleneck: str
    elements: list[StackElement]
    curatedAt: datetime
    validUntil: datetime | None = None


class InterventionVariant(BaseModel):
    hypothesisId: str
    intensity: VariantIntensity
    stack: IdentityStack
    generatedAt: datetime = Field(default_factory=datetime.utcnow)
