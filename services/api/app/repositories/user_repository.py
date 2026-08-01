"""User persistence / Clerk provisioning. Owner: Backend (A2)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def get_by_clerk_subject(db: Session, clerk_subject: str) -> User | None:
    return db.scalar(select(User).where(User.clerk_subject == clerk_subject))


def upsert_from_clerk(
    db: Session,
    *,
    clerk_subject: str,
    email: str | None = None,
    full_name: str | None = None,
    profile_image: str | None = None,
) -> tuple[User, bool]:
    """Return (user, created). Creates on first-seen ``sub``; refreshes profile + last_login_at."""
    now = datetime.now(timezone.utc)
    existing = get_by_clerk_subject(db, clerk_subject)
    if existing is None:
        user = User(
            id=str(uuid.uuid4()),
            clerk_subject=clerk_subject,
            email=email,
            full_name=full_name,
            profile_image=profile_image,
            capacity=100.0,
            last_login_at=now,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, True

    if email is not None and email != existing.email:
        existing.email = email
    if full_name is not None and full_name != existing.full_name:
        existing.full_name = full_name
    if profile_image is not None and profile_image != existing.profile_image:
        existing.profile_image = profile_image

    existing.last_login_at = now
    existing.updated_at = now
    db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing, False
