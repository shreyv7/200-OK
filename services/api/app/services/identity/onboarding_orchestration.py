"""Backend-owned wiring for the Mirror Interview. Owner: Backend. milestones.md M3.

FIXED_ONBOARDING_TOPICS is the fixed 5-question sequence from prd.md F1
verbatim (aspiration, why, current habits, biggest blocker, weekly
capacity) — a placeholder for AIA's real "4-6 question policy" (dynamic
follow-ups based on prior answers), which belongs in their Identity
Agent node (app/agents/nodes/identity/, currently empty). This module's
job is to prove the end-to-end flow works today; AIA's node replaces
the sequencing, not the extraction call itself.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.models.onboarding_turn import OnboardingTurn
from app.prompts.loader import load_prompt
from app.providers.llm.base import LLMProvider
from app.repositories import onboarding_repository, twin_repository
from app.schemas.identity import IdentityAttribute
from app.schemas.onboarding import OnboardingTurnResponse

FIXED_ONBOARDING_TOPICS: list[str] = [
    "What are you trying to become? (your aspiration)",
    "Why does that matter to you?",
    "What does your current day-to-day look like?",
    "What's the biggest thing blocking you right now?",
    "How much time can you realistically commit each week?",
]


class _ExtractionSchema(BaseModel):
    """What the LLM actually returns — attributes only, not the full
    persisted DeclaredSelf (id/userId/version/timestamps are Backend's
    to assign, not the model's to invent)."""

    attributes: list[IdentityAttribute]


def _format_transcript(turns: list[OnboardingTurn]) -> str:
    return "\n".join(f"{t.role}: {t.content}" for t in turns)


def _extract_attributes(llm_provider: LLMProvider, turns: list[OnboardingTurn]) -> list[IdentityAttribute]:
    template = load_prompt("identity/declared_self_extraction_v1")
    schema = _ExtractionSchema.model_json_schema()
    prompt = template.replace(
        "{interview_transcript}", _format_transcript(turns)
    ).replace("{output_schema_json}", json.dumps(schema))
    messages = [
        {"role": "system", "content": "You are the Trellis Identity Agent."},
        {"role": "user", "content": prompt},
    ]

    raw = llm_provider.generate_structured(schema=schema, messages=messages)
    try:
        return _ExtractionSchema.model_validate(raw).attributes
    except ValidationError as first_error:
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Your previous output was invalid: {first_error}. "
                    "Return valid JSON matching the schema exactly."
                ),
            }
        )
        raw_retry = llm_provider.generate_structured(schema=schema, messages=messages)
        return _ExtractionSchema.model_validate(raw_retry).attributes


def advance_turn(
    db: Session,
    llm_provider: LLMProvider,
    user_id: str,
    session_id: str | None,
    message: str,
) -> OnboardingTurnResponse:
    if session_id is None:
        session_row = onboarding_repository.create_session(db, user_id)
        onboarding_repository.append_turn(db, session_row.id, "assistant", FIXED_ONBOARDING_TOPICS[0])
        return OnboardingTurnResponse(
            sessionId=session_row.id,
            nextQuestion=FIXED_ONBOARDING_TOPICS[0],
            draft=None,
            done=False,
        )

    session_row = onboarding_repository.get_session(db, session_id)
    if session_row is None:
        raise ValueError(f"Unknown onboarding session: {session_id}")

    onboarding_repository.append_turn(db, session_id, "user", message)
    turns = onboarding_repository.list_turns(db, session_id)
    answered = len([t for t in turns if t.role == "user"])

    if answered < len(FIXED_ONBOARDING_TOPICS):
        next_question = FIXED_ONBOARDING_TOPICS[answered]
        onboarding_repository.append_turn(db, session_id, "assistant", next_question)
        return OnboardingTurnResponse(
            sessionId=session_id, nextQuestion=next_question, draft=None, done=False
        )

    attributes = _extract_attributes(llm_provider, turns)
    draft = twin_repository.upsert_draft(db, user_id, attributes)
    onboarding_repository.mark_completed(db, session_id)

    return OnboardingTurnResponse(sessionId=session_id, nextQuestion=None, draft=draft, done=True)
