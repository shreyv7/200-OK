from __future__ import annotations

from datetime import datetime, timezone

from app.agents.nodes.identity.node import IdentityAgentNode, interview_state_from_db_turns
from app.models.onboarding_turn import OnboardingTurn
from app.providers.llm.fake import FakeLLMProvider
from app.services.identity.onboarding_orchestration import advance_turn
from tests.conftest import ensure_user


def test_interview_state_from_db_turns_maps_roles(db_session) -> None:
    user_id = "onboard-map-user"
    ensure_user(db_session, user_id)
    now = datetime.now(timezone.utc)
    turns = [
        OnboardingTurn(session_id="s1", role="assistant", content="Q1", created_at=now),
        OnboardingTurn(session_id="s1", role="user", content="A1", created_at=now),
        OnboardingTurn(session_id="s1", role="assistant", content="Q2", created_at=now),
    ]
    state = interview_state_from_db_turns(user_id, turns)
    assert state.userId == user_id
    assert len(state.transcript) == 3
    assert state.transcript[0].speaker == "agent"
    assert state.transcript[1].speaker == "user"
    assert state.currentTurn == 2


def test_advance_turn_end_to_end_uses_agent_policy(db_session) -> None:
    user_id = "onboard-agent-user"
    ensure_user(db_session, user_id)
    llm = FakeLLMProvider()

    start = advance_turn(db_session, llm, user_id, session_id=None, message="")
    assert start.nextQuestion == IdentityAgentNode.QUESTION_POLICY[0]
    assert start.done is False

    session_id = start.sessionId
    answers = [
        "Public speaker",
        "Career growth",
        "Weekly commits",
        "Short-form distraction",
        "10 hours",
    ]
    for i, answer in enumerate(answers):
        response = advance_turn(db_session, llm, user_id, session_id, answer)
        if i < len(answers) - 1:
            assert response.done is False
            assert response.nextQuestion == IdentityAgentNode.QUESTION_POLICY[i + 1]
        else:
            assert response.done is True
            assert response.draft is not None
