"""Growth Partner Match contract. Owner: Backend. F10 (prd.md), milestones.md M8."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PartnerProfile(BaseModel):
    id: str
    name: str
    stage: str
    goal: str
    matchReason: str
    similarity: float | None = None
    sourceBadge: str | None = None
    prototype: bool = Field(
        default=True,
        description="True when ranking used local/fake embeddings rather than Qdrant Cloud.",
    )
