"""Lattice strut contributor contract. Owner: Backend. F3 lattice-click popover."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LatticeContributor(BaseModel):
    eventId: str
    type: str
    timestamp: datetime
    deltaDays: float
    baseWeight: float
    value: float
    decayFactor: float
    decayedContribution: float
    source: str
    simulated: bool


class LatticeStrutResponse(BaseModel):
    attrId: str
    attrLabel: str
    weight: float
    targetWeeklyPoints: float
    revealedPoints: float
    deficit: float
    creationContribution: float
    passiveContribution: float
    driftContribution: float
    contributingEvents: list[LatticeContributor]
