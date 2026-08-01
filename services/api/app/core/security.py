"""Clerk JWT authentication. Owner: Backend (A1).

Replaces the M0 ``501`` stub with real JWKS verification. ``auth_bypass`` remains
available only when ``ENV=local`` (pytest / local smoke). User-row provisioning
beyond ``clerk_subject`` mapping is A2.
"""

from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.models.user import User
from app.services.authentication import verify_clerk_session_token


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise _unauthorized("Missing credentials")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("Invalid Authorization header")
    return token


def _resolve_user_id_for_clerk_subject(db: Session, clerk_subject: str) -> str:
    """Map verified Clerk ``sub`` → internal ``users.id``.

    Looks up ``clerk_subject``; creates a minimal row on first sight so verified
    tokens are usable before A2 lands email / last_login_at enrichment.
    """
    existing = db.scalar(select(User).where(User.clerk_subject == clerk_subject))
    if existing is not None:
        return existing.id

    user = User(id=str(uuid.uuid4()), clerk_subject=clerk_subject, capacity=100.0)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id


def get_current_user_id(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> str:
    # Bypass is local/pytest only — never honored outside ENV=local.
    if settings.env == "local" and settings.auth_bypass:
        return settings.demo_user_id

    token = _extract_bearer_token(authorization)

    try:
        claims = verify_clerk_session_token(token, settings)
    except jwt.PyJWTError as exc:
        raise _unauthorized("Invalid or expired session") from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    sub = claims.get("sub")
    if not sub:
        raise _unauthorized("Invalid or expired session")

    return _resolve_user_id_for_clerk_subject(db, str(sub))
