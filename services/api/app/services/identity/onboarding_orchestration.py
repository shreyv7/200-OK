"""Backend-owned wiring for the Mirror Interview. Owner: Backend. milestones.md M3.

Routes turn policy and structured extraction through AIA's IdentityAgentNode
(app/agents/nodes/identity/). This module persists transcript turns and
maps agent output to API responses — it does not duplicate question policy
or extraction prompts.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.nodes.identity.node import IdentityAgentNode, interview_state_from_db_turns
from app.providers.llm.base import LLMProvider
from app.repositories import onboarding_repository, twin_repository
from app.schemas.onboarding import OnboardingTurnResponse

_identity_agent = IdentityAgentNode()

# Backwards-compatible alias for tests/docs referencing PRD F1 question order.
FIXED_ONBOARDING_TOPICS: list[str] = list(IdentityAgentNode.QUESTION_POLICY)


def advance_turn(
    db: Session,
    llm_provider: LLMProvider,
    user_id: str,
    session_id: str | None,
    message: str,
    answer_kind: str | None = None,
) -> OnboardingTurnResponse:
    if session_id is None:
        session_row = onboarding_repository.create_session(db, user_id)
        first_question = _identity_agent.generate_next_interview_question(
            interview_state_from_db_turns(user_id, []),
            llm_provider,
        )
        onboarding_repository.append_turn(db, session_row.id, "assistant", first_question)
        return OnboardingTurnResponse(
            sessionId=session_row.id,
            nextQuestion=first_question,
            draft=None,
            done=False,
        )

    if not message.strip():
        raise ValueError("Answer cannot be empty.")

    session_row = onboarding_repository.get_session_for_user(db, session_id, user_id)
    if session_row is None:
        raise ValueError(f"Unknown onboarding session: {session_id}")

    kind = answer_kind if answer_kind in {"preset", "freeform"} else "freeform"
    onboarding_repository.append_turn(
        db, session_id, "user", message.strip(), answer_kind=kind
    )
    turns = onboarding_repository.list_turns(db, session_id)
    state = interview_state_from_db_turns(user_id, turns)
    answered = sum(1 for turn in turns if turn.role == "user")

    if answered < _identity_agent.max_turns:
        state.currentTurn = answered + 1
        next_question = _identity_agent.generate_next_interview_question(state, llm_provider)
        onboarding_repository.append_turn(db, session_id, "assistant", next_question)
        return OnboardingTurnResponse(
            sessionId=session_id,
            nextQuestion=next_question,
            draft=None,
            done=False,
        )

    try:
        attributes = _identity_agent.extract_attributes(state, llm_provider)
    except Exception:
        # Budget/LLM/schema failures must not brick Mirror Interview extraction.
        # Prefer the agent's deterministic degraded Declared Self over a 500.
        from app.schemas.identity import IdentityAttribute

        fallback = _identity_agent._fallback_extraction_dict()
        attributes = [IdentityAttribute.model_validate(a) for a in fallback["attributes"]]

    draft = twin_repository.upsert_draft(db, user_id, attributes)
    onboarding_repository.mark_completed(db, session_id)

    return OnboardingTurnResponse(sessionId=session_id, nextQuestion=None, draft=draft, done=True)
