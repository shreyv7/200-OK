"""Deterministic Guardian gate — AIS M5."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from app.services.identity.scoring.constants import CAPACITY_FULL_MIN, CAPACITY_LIGHT_MIN
from app.services.recommendation.guardian_constants import (
    DISMISSAL_RATE_CEILING,
    INTERVENTION_DAILY_CAP,
    MIN_INTERVENTION_SPACING_MINUTES,
)

GuardianAction = Literal["deliver", "downgrade", "delay", "cancel"]
VariantIntensity = Literal["full", "light", "micro"]

_REASON_COPY: dict[str, str] = {
    "daily_cap": "You've had five interventions today. We'll pause until tomorrow.",
    "too_soon": "We'll wait a bit before the next intervention.",
    "high_dismissal": "Recent dismissals suggest easing off; trying a lighter approach.",
    "capacity_low": "Capacity changed; preserving momentum without adding load.",
    "deliver": "Intervention cleared for delivery.",
}


@dataclass
class GuardianContext:
    capacity_pct: int = 100
    interventions_today: int = 0
    last_intervention_at: datetime | None = None
    recent_dismissal_rate: float = 0.0
    now: datetime | None = None


@dataclass
class GuardianDecision:
    action: GuardianAction
    intensity: VariantIntensity
    reason_code: str
    reason: str


def capacity_to_intensity(capacity_pct: int) -> VariantIntensity:
    if capacity_pct >= CAPACITY_FULL_MIN:
        return "full"
    if capacity_pct >= CAPACITY_LIGHT_MIN:
        return "light"
    return "micro"


def evaluate_guardian(context: GuardianContext) -> GuardianDecision:
    """Tier-0 deterministic gate — no LLM."""
    now = context.now or datetime.now(timezone.utc)
    intensity = capacity_to_intensity(context.capacity_pct)

    if context.interventions_today >= INTERVENTION_DAILY_CAP:
        return GuardianDecision(
            action="cancel",
            intensity=intensity,
            reason_code="daily_cap",
            reason=_REASON_COPY["daily_cap"],
        )

    if context.last_intervention_at is not None:
        elapsed = now - context.last_intervention_at
        if elapsed < timedelta(minutes=MIN_INTERVENTION_SPACING_MINUTES):
            return GuardianDecision(
                action="delay",
                intensity=intensity,
                reason_code="too_soon",
                reason=_REASON_COPY["too_soon"],
            )

    if context.recent_dismissal_rate >= DISMISSAL_RATE_CEILING:
        return GuardianDecision(
            action="downgrade",
            intensity="light" if intensity == "full" else "micro",
            reason_code="high_dismissal",
            reason=_REASON_COPY["high_dismissal"],
        )

    if intensity != "full":
        return GuardianDecision(
            action="downgrade",
            intensity=intensity,
            reason_code="capacity_low",
            reason=_REASON_COPY["capacity_low"],
        )

    return GuardianDecision(
        action="deliver",
        intensity="full",
        reason_code="deliver",
        reason=_REASON_COPY["deliver"],
    )
