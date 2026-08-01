"""Onboarding (Mirror Interview) contracts. Owner: Backend. F1 (prd.md), milestones.md M3."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.identity import DeclaredSelf, IdentityAttribute


class OnboardingTurnRequest(BaseModel):
    sessionId: str | None = None
    message: str = ""  # ignored when sessionId is None (starts a new session)


class OnboardingTurnResponse(BaseModel):
    sessionId: str
    nextQuestion: str | None = None
    draft: DeclaredSelf | None = None
    done: bool = False


class IdentityPatchRequest(BaseModel):
    attributes: list[IdentityAttribute]
    confirm: bool = False
