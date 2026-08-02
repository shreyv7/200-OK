from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.agents.nodes.identity.node import IdentityAgentNode, interview_state_from_db_turns
from app.models.onboarding_turn import OnboardingTurn
from app.providers.llm.fake import FakeLLMProvider
from app.repositories import onboarding_repository
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


def test_advance_turn_persists_freeform_answer_kind(db_session) -> None:
    user_id = "onboard-freeform-user"
    ensure_user(db_session, user_id)
    llm = FakeLLMProvider()

    start = advance_turn(db_session, llm, user_id, session_id=None, message="")
    advance_turn(
        db_session,
        llm,
        user_id,
        start.sessionId,
        "I want to ship a consumer AI writing tool for founders",
        answer_kind="freeform",
    )
    turns = onboarding_repository.list_turns(db_session, start.sessionId)
    user_turns = [t for t in turns if t.role == "user"]
    assert len(user_turns) == 1
    assert user_turns[0].answer_kind == "freeform"
    assert "consumer AI" in user_turns[0].content


def test_advance_turn_rejects_empty_answer(db_session) -> None:
    user_id = "onboard-empty-user"
    ensure_user(db_session, user_id)
    llm = FakeLLMProvider()
    start = advance_turn(db_session, llm, user_id, session_id=None, message="")

    with pytest.raises(ValueError, match="empty"):
        advance_turn(db_session, llm, user_id, start.sessionId, "   ")
