"""Trust Ledger entry — owned by AIS reflection rules; stored/served by Backend."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

LedgerVerdict = Literal["worked", "failed", "pending"]
LedgerAction = Literal["delivered", "accepted", "snoozed", "dismissed", "completed"]


class LedgerEntry(BaseModel):
    id: str
    userId: str
    hypothesisId: str
    hypothesisFamily: str
    action: LedgerAction
    verdict: LedgerVerdict = "pending"
    timestamp: datetime
    unlearningTriggered: bool = False
    lensWeightAdjustment: dict[str, float] | None = None
    note: str | None = None
