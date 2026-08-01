"""Weekly Report + Identity Evolution contracts. Owner: Backend. F8/F11 (prd.md), milestones.md M7."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.identity import IdentityAttribute

AgentRunType = Literal["weekly_report", "evolution"]
EvolutionStatus = Literal["pending", "accepted", "rejected"]


class AgentRunRequest(BaseModel):
    type: AgentRunType


class WeeklyReport(BaseModel):
    narrative: str
    generatedAt: datetime = Field(default_factory=datetime.utcnow)


class IdentityEvolutionProposal(BaseModel):
    id: str
    userId: str
    proposedAttributes: list[IdentityAttribute]
    citedEvidenceIds: list[str] = Field(default_factory=list)
    rationale: str
    status: EvolutionStatus = "pending"
    createdAt: datetime = Field(default_factory=datetime.utcnow)


class AgentRunResult(BaseModel):
    runId: str
    type: AgentRunType
    weeklyReport: WeeklyReport | None = None
    evolutionProposal: IdentityEvolutionProposal | None = None
