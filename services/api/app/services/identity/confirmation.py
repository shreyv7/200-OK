"""Confirmation and Consent Payload module for AIA ("Did I get you right?").

Assembles user review card DTO for extracted DeclaredSelf identity targets.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.identity import DeclaredSelf, IdentityAttribute


@dataclass
class InterviewTurn:
    turnIndex: int
    speaker: str  # "agent" or "user"
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class InterviewState:
    userId: str
    currentTurn: int = 1
    maxTurns: int = 5
    transcript: List[InterviewTurn] = field(default_factory=list)
    isComplete: bool = False


@dataclass
class ConfirmationPayload:
    userId: str
    declaredSelf: DeclaredSelf
    summaryNarrative: str
    attributeBreakdown: List[Dict[str, Any]]
    weightSumValid: bool
    promptMessage: str = "Did I get you right? Review your identity targets below before confirming."


def build_confirmation_payload(user_id: str, declared_self: DeclaredSelf) -> ConfirmationPayload:
    """Assembles ConfirmationPayload for user consent/review card before setting active Twin."""
    total_w = sum(attr.weight for attr in declared_self.attributes)
    weight_valid = abs(total_w - 1.0) < 1e-4

    attr_breakdowns: List[Dict[str, Any]] = []
    labels: List[str] = []

    for attr in declared_self.attributes:
        labels.append(attr.label)
        attr_breakdowns.append({
            "id": attr.id,
            "label": attr.label,
            "weightPercentage": round(attr.weight * 100.0, 1),
            "targetWeeklyPoints": attr.targetWeeklyPoints,
            "markerCount": len(attr.markers),
            "markers": [{"id": m.id, "label": m.label, "description": m.description} for m in attr.markers],
        })

    summary = (
        f"You declared a focus on becoming a {', '.join(labels[:2])}. "
        f"We've structured {len(declared_self.attributes)} identity attributes with weekly target points."
    )

    return ConfirmationPayload(
        userId=user_id,
        declaredSelf=declared_self,
        summaryNarrative=summary,
        attributeBreakdown=attr_breakdowns,
        weightSumValid=weight_valid,
        promptMessage="Did I get you right? Review your identity targets below before confirming.",
    )
