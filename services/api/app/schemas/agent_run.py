"""Agent run request/result envelope. Owner: Backend. F8/F11 (prd.md), milestones.md M7/M8.

M8 fix: WeeklyReport/IdentityEvolutionProposal used to be duplicated
here with different shapes than AIA's real generation output
(app.schemas.report / app.schemas.evolution). Deleted the duplicates —
this module now only wraps AIA's schemas in a run envelope.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.schemas.evolution import IdentityEvolutionProposal
from app.schemas.report import WeeklyReport

AgentRunType = Literal["weekly_report", "evolution"]


class AgentRunRequest(BaseModel):
    type: AgentRunType


class AgentRunResult(BaseModel):
    runId: str
    type: AgentRunType
    weeklyReport: WeeklyReport | None = None
    evolutionProposal: IdentityEvolutionProposal | None = None
