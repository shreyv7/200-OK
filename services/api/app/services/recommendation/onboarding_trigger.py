"""Onboarding confirm event — AIS consume seam (promote to app.schemas if Backend asks)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.services.recommendation.gap_snapshot import GapSnapshot


@dataclass(frozen=True)
class OnboardingConfirmEvent:
    userId: str
    twinVersion: int
    confirmedAt: str
    gapSnapshot: GapSnapshot | None = None
    trigger: Literal["onboarding.confirmed"] = "onboarding.confirmed"
