"""Onboarding (Mirror Interview) contracts. Owner: Backend. F1 (prd.md), milestones.md M3."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.identity import DeclaredSelf, IdentityAttribute


class OnboardingTurnRequest(BaseModel):
    sessionId: str | None = None
    message: str = ""  # ignored when sessionId is None (starts a new session)
    personaId: str | None = None


class OnboardingQuestion(BaseModel):
    id: str
    prompt: str
    hint: str
    options: list[str] = Field(min_length=2)


class OnboardingPersona(BaseModel):
    id: str
    title: str
    description: str
    outcome: str
    questions: list[OnboardingQuestion] = Field(min_length=4, max_length=6)


class OnboardingTurnResponse(BaseModel):
    sessionId: str
    nextQuestion: str | None = None
    draft: DeclaredSelf | None = None
    done: bool = False


class IdentityPatchRequest(BaseModel):
    attributes: list[IdentityAttribute]
    confirm: bool = False
