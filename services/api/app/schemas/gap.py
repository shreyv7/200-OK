"""Gap breakdown DTO — formula owned by AIA (prd.md §9); Backend hosts/serves the result."""

from __future__ import annotations

from pydantic import BaseModel


class AttributeContribution(BaseModel):
    attributeId: str
    w_i: float
    D_i: float
    R_i: float
    deficit_i: float


class GapBreakdown(BaseModel):
    userId: str
    gapScore: float
    alignmentScore: float
    createPoints: float
    consumePoints: float
    driftPoints: float
    createConsumeRatio: float
    consistency: float
    momentum: float
    attributes: list[AttributeContribution]
