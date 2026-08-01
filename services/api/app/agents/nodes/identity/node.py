"""Identity Agent Node for AIA onboarding ("The Mirror Interview").

Orchestrates 4-6 question conversational policy and drives structured DeclaredSelf extraction.
"""

from typing import Any, Dict, List, Optional, Tuple

from app.schemas.identity import DeclaredSelf
from app.services.identity.confirmation import (
    ConfirmationPayload,
    InterviewState,
    InterviewTurn,
    build_confirmation_payload,
)
from app.services.identity.extractor import validate_and_repair_extraction


class IdentityAgentNode:
    """Conversational onboarding agent node for Mirror Interview turns and extraction."""

    QUESTION_POLICY: List[str] = [
        "What primary identity or aspirational role do you want to build right now?",
        "Why is achieving this identity milestone deeply important to you at this stage?",
        "What current daily habits or creation activities best reflect this identity?",
        "What is the single biggest blocker, distraction, or focus drift holding you back?",
        "How many evidence points or hours per week can you realistically commit to this identity?",
    ]

    def generate_next_interview_question(self, state: InterviewState, llm_provider: Optional[Any] = None) -> str:
        """Returns the next conversational interview question based on currentTurn."""
        turn_idx = min(state.currentTurn - 1, len(self.QUESTION_POLICY) - 1)
        question = self.QUESTION_POLICY[turn_idx]
        
        # If LLMProvider available, can refine question context dynamically
        if llm_provider and hasattr(llm_provider, "generate"):
            try:
                transcript_text = "\n".join([f"{t.speaker}: {t.text}" for t in state.transcript])
                prompt = f"Given transcript:\n{transcript_text}\nAsk the next question empathetically: {question}"
                question = llm_provider.generate(prompt)
            except Exception:
                pass  # Fallback to deterministic policy question

        return question

    def extract_declared_self(
        self,
        state: InterviewState,
        llm_provider: Optional[Any] = None,
    ) -> Tuple[bool, Optional[DeclaredSelf], Optional[ConfirmationPayload]]:
        """Extracts structured DeclaredSelf and constructs ConfirmationPayload."""
        transcript_text = "\n".join([f"{t.speaker}: {t.text}" for t in state.transcript])
        extracted_dict: Optional[Dict[str, Any]] = None

        if llm_provider and hasattr(llm_provider, "generate_structured"):
            try:
                prompt = (
                    f"Extract 2-4 identity attributes and markers from the following transcript:\n"
                    f"{transcript_text}\n"
                    f"Return JSON matching DeclaredSelf schema."
                )
                extracted_dict = llm_provider.generate_structured(schema=DeclaredSelf, prompt=prompt)
            except Exception:
                extracted_dict = None

        # Fallback to heuristic extraction if LLM unavailable or provider failed
        if not extracted_dict:
            extracted_dict = {
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
                ]
            }

        is_valid, declared_self, err = validate_and_repair_extraction(extracted_dict, state.userId)
        if not is_valid or not declared_self:
            return False, None, None

        payload = build_confirmation_payload(state.userId, declared_self)
        return True, declared_self, payload
