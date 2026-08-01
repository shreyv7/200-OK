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

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.onboarding_turn import OnboardingTurn
from app.prompts.loader import build_messages
from app.providers.llm.base import LLMProvider
from app.providers.llm.repair import generate_structured_with_repair
from app.repositories import onboarding_repository, twin_repository
from app.schemas.identity import IdentityAttribute
from app.schemas.onboarding import OnboardingTurnResponse
from app.services.identity.onboarding_personas import get_persona, get_persona_from_context

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


def _validate_extraction_response(raw: object) -> _ExtractionSchema:
    """B6 (docs/work.md): raises pydantic.ValidationError on a malformed
    response so generate_structured_with_repair() knows to retry once —
    this was the original hand-rolled retry-once pattern (B1) that B4's
    shared helper was extracted from; folded onto that shared helper here
    so this call site matches the other three instead of maintaining its
    own copy of the same retry logic."""
    return _ExtractionSchema.model_validate(raw)


def _extract_attributes(llm_provider: LLMProvider, turns: list[OnboardingTurn]) -> list[IdentityAttribute]:
    schema = _ExtractionSchema.model_json_schema()
    messages = build_messages(
        "identity/declared_self_extraction_v1",
        interview_transcript=_format_transcript(turns),
        output_schema_json=json.dumps(schema),
    )
    validated = generate_structured_with_repair(llm_provider, schema, messages, _validate_extraction_response)
    return validated.attributes


def advance_turn(
    db: Session,
    llm_provider: LLMProvider,
    user_id: str,
    session_id: str | None,
    message: str,
    persona_id: str | None = None,
) -> OnboardingTurnResponse:
    if session_id is None:
        persona = get_persona(persona_id)
        if persona_id is not None and persona is None:
            raise ValueError(f"Unknown onboarding persona: {persona_id}")
        topics = persona.questions if persona is not None else FIXED_ONBOARDING_TOPICS
        session_row = onboarding_repository.create_session(db, user_id)
        if persona is not None:
            onboarding_repository.append_turn(
                db, session_row.id, "assistant",
                f"Selected onboarding path: {persona.title}. Intended outcome: {persona.outcome}",
            )
        first_question = topics[0].prompt if persona is not None else topics[0]
        onboarding_repository.append_turn(db, session_row.id, "assistant", first_question)
        return OnboardingTurnResponse(
            sessionId=session_row.id,
            nextQuestion=first_question,
            draft=None,
            done=False,
        )

    session_row = onboarding_repository.get_session_for_user(db, session_id, user_id)
    if session_row is None:
        raise ValueError(f"Unknown onboarding session: {session_id}")

    onboarding_repository.append_turn(db, session_id, "user", message)
    turns = onboarding_repository.list_turns(db, session_id)
    answered = len([t for t in turns if t.role == "user"])

    persona_context = next((t.content for t in turns if t.content.startswith("Selected onboarding path:")), None)
    persona = get_persona_from_context(persona_context)
    topics = persona.questions if persona is not None else FIXED_ONBOARDING_TOPICS
    if answered < len(topics):
        next_question = topics[answered].prompt if persona is not None else topics[answered]
        onboarding_repository.append_turn(db, session_id, "assistant", next_question)
        return OnboardingTurnResponse(
            sessionId=session_id, nextQuestion=next_question, draft=None, done=False
        )

    attributes = _extract_attributes(llm_provider, turns)
    draft = twin_repository.upsert_draft(db, user_id, attributes)
    onboarding_repository.mark_completed(db, session_id)

    return OnboardingTurnResponse(sessionId=session_id, nextQuestion=None, draft=draft, done=True)
