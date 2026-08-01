"""Guardian Decision module for AIA (PRD §6 F6 Protection Layer).

Provides deterministic, rule-based evaluation of intervention delivery requests
returning structured reason codes and plain-language explanation templates.
LLMs NEVER decide cancel/downgrade/delay actions.
"""

from dataclasses import dataclass
from typing import Literal, Optional

from app.services.identity.scoring.constants import (
    CAPACITY_LIGHT_MIN,
    HIGH_DISMISSAL_RATE_THRESHOLD,
    INTERVENTION_DAILY_CAP,
    INTERVENTION_MIN_SPACING_HOURS,
)

GuardianAction = Literal["allow", "downgrade", "delay", "cancel"]


@dataclass
class GuardianDecision:
    action: GuardianAction
    reason_code: str
    plain_language_reason: str
    intensity: str  # "full" | "light" | "micro"


def _step_down_intensity(current: str) -> str:
    if current == "full":
        return "light"
    return "micro"


def evaluate_guardian_action(
    capacity_pct: int = 100,
    interventions_today: int = 0,
    dismissal_rate: float = 0.0,
    hours_since_last_intervention: Optional[float] = None,
    current_intensity: str = "full",
) -> GuardianDecision:
    """Evaluates intervention delivery against Guardian budget, capacity, and dismissal rules."""
    # Priority 1: Daily intervention cap reached -> Cancel
    if interventions_today >= INTERVENTION_DAILY_CAP:
        return GuardianDecision(
            action="cancel",
            reason_code="daily_cap_reached",
            plain_language_reason="You've had 5 growth touchpoints today. Rest is growth too.",
            intensity=current_intensity,
        )

    # Priority 2: Too frequent intervention -> Delay
    if hours_since_last_intervention is not None and hours_since_last_intervention < INTERVENTION_MIN_SPACING_HOURS:
        return GuardianDecision(
            action="delay",
            reason_code="too_frequent",
            plain_language_reason="Last intervention was recent. Giving you space before the next step.",
            intensity=current_intensity,
        )

    # Priority 3: High dismissal rate -> Downgrade intensity
    if dismissal_rate >= HIGH_DISMISSAL_RATE_THRESHOLD and current_intensity != "micro":
        new_intensity = _step_down_intensity(current_intensity)
        return GuardianDecision(
            action="downgrade",
            reason_code="high_dismissal_rate",
            plain_language_reason="You've been skipping recent suggestions. Switching to a lighter touch.",
            intensity=new_intensity,
        )

    # Priority 4: Low capacity slider -> Downgrade intensity to micro
    if capacity_pct < CAPACITY_LIGHT_MIN:
        return GuardianDecision(
            action="downgrade",
            reason_code="low_capacity",
            plain_language_reason="Capacity changed; preserving momentum without adding load.",
            intensity="micro",
        )

    # Priority 5: All checks pass -> Allow
    return GuardianDecision(
        action="allow",
        reason_code="ok",
        plain_language_reason="",
        intensity=current_intensity,
    )
