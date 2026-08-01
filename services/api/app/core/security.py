"""Clerk JWT authentication + user provisioning. Owner: Backend (A1/A2).

A1: JWKS verification. A2: upsert ``User`` by ``clerk_subject`` with email /
``last_login_at``. ``auth_bypass`` remains local/pytest only.
"""

from __future__ import annotations

import logging

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.models.user import User
from app.repositories import user_repository
from app.services.authentication import verify_clerk_session_token
from app.services.authentication.clerk_profile import resolve_profile

logger = logging.getLogger(__name__)


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


def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> User:
    # Bypass is local/pytest only — never honored outside ENV=local.
    if settings.env == "local" and settings.auth_bypass:
        user = user_repository.get_by_id(db, settings.demo_user_id)
        if user is None:
            user = User(id=settings.demo_user_id, capacity=100.0, email="aarav@demo.local")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    token = _extract_bearer_token(authorization)

    try:
        claims = verify_clerk_session_token(token, settings)
    except jwt.PyJWTError as exc:
        logger.warning("Clerk JWT rejected: %s", exc)
        detail = "Invalid or expired session"
        if settings.env == "local":
            detail = f"Invalid or expired session ({exc})"
        raise _unauthorized(detail) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    sub = claims.get("sub")
    if not sub:
        raise _unauthorized("Invalid or expired session")

    profile = resolve_profile(claims, settings)
    user, _created = user_repository.upsert_from_clerk(
        db,
        clerk_subject=str(sub),
        email=profile.email,
        full_name=profile.full_name,
        profile_image=profile.profile_image,
    )
    return user


def get_current_user_id(user: User = Depends(get_current_user)) -> str:
    return user.id
