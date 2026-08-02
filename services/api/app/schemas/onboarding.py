"""Onboarding (Mirror Interview) contracts. Owner: Backend. F1 (prd.md), milestones.md M3."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.identity import DeclaredSelf, IdentityAttribute

AnswerKind = Literal["preset", "freeform"]


class OnboardingTurnRequest(BaseModel):
    sessionId: str | None = None
    message: str = Field(default="", max_length=2000)
    # Ignored when starting a session. For user answers: quick-pick vs typed.
    answerKind: AnswerKind | None = None

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        return value.strip()


class OnboardingTurnResponse(BaseModel):
    sessionId: str
    nextQuestion: str | None = None
    draft: DeclaredSelf | None = None
    done: bool = False


class IdentityPatchRequest(BaseModel):
    attributes: list[IdentityAttribute]
    confirm: bool = False
