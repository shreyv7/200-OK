"""Identity Agent Node for AIA onboarding ("The Mirror Interview").

Orchestrates 4-6 question conversational policy and drives structured DeclaredSelf extraction.
"""

from __future__ import annotations

import json
from typing import Any, Optional, Tuple

from pydantic import BaseModel

from app.models.onboarding_turn import OnboardingTurn
from app.prompts.loader import build_messages
from app.providers.llm.base import LLMProvider
from app.providers.llm.repair import generate_structured_with_repair
from app.schemas.identity import DeclaredSelf, IdentityAttribute
from app.services.identity.confirmation import (
    ConfirmationPayload,
    InterviewState,
    InterviewTurn,
    build_confirmation_payload,
)
from app.services.identity.extractor import validate_and_repair_extraction


class _ExtractionSchema(BaseModel):
    """LLM output shape — attributes only; Backend assigns userId/version."""

    attributes: list[IdentityAttribute]


class IdentityAgentNode:
    """Conversational onboarding agent node for Mirror Interview turns and extraction."""

    QUESTION_POLICY: list[str] = [
        "What primary identity or aspirational role do you want to build right now?",
        "Why is achieving this identity milestone deeply important to you at this stage?",
        "What current daily habits or creation activities best reflect this identity?",
        "What is the single biggest blocker, distraction, or focus drift holding you back?",
        "How many evidence points or hours per week can you realistically commit to this identity?",
    ]

    @property
    def max_turns(self) -> int:
        return len(self.QUESTION_POLICY)

    def generate_next_interview_question(
        self,
        state: InterviewState,
        llm_provider: LLMProvider | None = None,
    ) -> str:
        """Return the next conversational interview question based on currentTurn."""
        _ = llm_provider  # reserved for empathetic rephrasing via structured LLM later
        turn_idx = min(max(state.currentTurn, 1) - 1, len(self.QUESTION_POLICY) - 1)
        return self.QUESTION_POLICY[turn_idx]

    def extract_attributes(
        self,
        state: InterviewState,
        llm_provider: LLMProvider,
    ) -> list[IdentityAttribute]:
        """Production extraction via declared_self_extraction_v1 + repair pass."""
        schema = _ExtractionSchema.model_json_schema()
        transcript = "\n".join(f"{t.speaker}: {t.text}" for t in state.transcript)
        messages = build_messages(
            "identity/declared_self_extraction_v1",
            interview_transcript=transcript,
            output_schema_json=json.dumps(schema),
        )
        validated = generate_structured_with_repair(
            llm_provider,
            schema,
            messages,
            lambda raw: _ExtractionSchema.model_validate(raw),
        )
        return validated.attributes

    def extract_declared_self(
        self,
        state: InterviewState,
        llm_provider: LLMProvider | None = None,
    ) -> Tuple[bool, Optional[DeclaredSelf], Optional[ConfirmationPayload]]:
        """Extract structured DeclaredSelf and build the consent confirmation payload."""
        if llm_provider is None:
            return False, None, None

        try:
            attributes = self.extract_attributes(state, llm_provider)
            extracted_dict: dict[str, Any] = {"version": 1, "attributes": [a.model_dump() for a in attributes]}
        except Exception:
            extracted_dict = self._fallback_extraction_dict()

        is_valid, declared_self, _err = validate_and_repair_extraction(extracted_dict, state.userId)
        if not is_valid or not declared_self:
            return False, None, None

        payload = build_confirmation_payload(state.userId, declared_self)
        return True, declared_self, payload

    @staticmethod
    def _fallback_extraction_dict() -> dict[str, Any]:
        """Deterministic degraded path when structured extraction fails."""
        return {
            "version": 1,
            "attributes": [
                {
                    "id": "public_speaker",
                    "label": "Public Speaker",
                    "weight": 0.5,
                    "targetWeeklyPoints": 15.0,
                    "markers": [{"id": "m1", "label": "Record speaking practice"}],
                },
                {
                    "id": "builder",
                    "label": "Builder Who Ships",
                    "weight": 0.5,
                    "targetWeeklyPoints": 15.0,
                    "markers": [{"id": "m2", "label": "GitHub Commit"}],
                },
            ],
        }


def interview_state_from_db_turns(user_id: str, turns: list[OnboardingTurn]) -> InterviewState:
    """Map persisted onboarding transcript rows to InterviewState."""
    transcript: list[InterviewTurn] = []
    current_index = 0
    for row in turns:
        if row.role == "assistant":
            current_index += 1
        speaker = "agent" if row.role == "assistant" else "user"
        transcript.append(
            InterviewTurn(
                turnIndex=current_index,
                speaker=speaker,
                text=row.content,
                timestamp=row.created_at,
            )
        )

    user_answers = sum(1 for row in turns if row.role == "user")
    max_turns = len(IdentityAgentNode.QUESTION_POLICY)
    return InterviewState(
        userId=user_id,
        currentTurn=min(user_answers + 1, max_turns),
        maxTurns=max_turns,
        transcript=transcript,
        isComplete=user_answers >= max_turns,
    )
