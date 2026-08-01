"""Growth Partner Match contract. Owner: Backend. F10 (prd.md, P2 mock only), milestones.md M8."""

from __future__ import annotations

from pydantic import BaseModel


class PartnerProfile(BaseModel):
    id: str
    name: str
    stage: str
    goal: str
    matchReason: str
    prototype: bool = True
