"""Clerk JWT verification stub. Owner: Backend.

Local dev bypass only. Real Clerk JWKS verification is not implemented in M0 —
tracked as a follow-up once Clerk keys are available (see plan Open Question 3
in anvi/plan-m0-backend.md history).
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


def get_current_user_id(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> str:
    if settings.env == "local" and settings.auth_bypass:
        return settings.demo_user_id

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Clerk JWT verification not yet implemented outside local bypass",
    )
