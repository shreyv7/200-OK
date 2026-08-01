"""EvidenceEvent contract — owned by Backend (see prd.md §7, techstack.md §15.1)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SourceProvider = Literal["github", "google_calendar", "youtube", "notion", "trellis"]
EventCategory = Literal["creation", "passive_learning", "focus_drift", "reflection"]


class EvidenceEvent(BaseModel):
    id: str
    userId: str
    timestamp: datetime
    source: SourceProvider
    type: str
    category: EventCategory
    identityAttributeIds: list[str] = Field(default_factory=list)
    value: float
    baseWeight: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    simulated: bool = False


class RawMCPPayload(BaseModel):
    sourceProvider: SourceProvider
    rawPayload: dict[str, Any]


class EvidenceIngestBody(BaseModel):
    """Public POST /api/v1/evidence body — no client-supplied userId (A3)."""

    timestamp: datetime
    source: SourceProvider
    type: str
    category: EventCategory
    identityAttributeIds: list[str] = Field(default_factory=list)
    value: float
    baseWeight: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    simulated: bool = False


class EvidenceIngestRequest(EvidenceIngestBody):
    """Internal ingest shape used by services/seed/simulator after auth attribution."""

    userId: str
