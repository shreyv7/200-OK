"""Declared Self / Twin contract — shape defined for AIA to fill; persisted by Backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class IdentityMarker(BaseModel):
    id: str
    label: str
    description: str | None = None


class IdentityAttribute(BaseModel):
    id: str
    label: str
    weight: float = Field(ge=0.0, le=1.0)
    targetWeeklyPoints: float = Field(description="D_i in the Gap formula (prd.md §9)")
    markers: list[IdentityMarker] = Field(default_factory=list)


class DeclaredSelf(BaseModel):
    id: str
    userId: str
    version: int
    attributes: list[IdentityAttribute]
    createdAt: datetime
    confirmedAt: datetime | None = None
