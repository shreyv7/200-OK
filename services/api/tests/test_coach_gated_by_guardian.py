from __future__ import annotations

from app.agents.nodes.coach.node import coach_node


def _state(*, action: str = "deliver", capacity_pct: int = 80, delivery_allowed: bool = True) -> dict:
    return {
        "guardian_decision": {"action": action, "intensity": "full"},
        "capacity_pct": capacity_pct,
        "delivery_allowed": delivery_allowed,
    }


def test_coach_silent_on_cancel_and_delay() -> None:
    assert "coach_message" not in coach_node(_state(action="cancel"))
    assert "coach_message" not in coach_node(_state(action="delay"))


def test_coach_silent_on_low_capacity() -> None:
    assert "coach_message" not in coach_node(_state(capacity_pct=20))


def test_coach_present_when_guardian_delivers() -> None:
    result = coach_node(_state(action="deliver", capacity_pct=80))
    assert result["coach_message"]["text"]
    assert result["coach_message"]["intensity"] == "full"
