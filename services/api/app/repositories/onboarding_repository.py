"""Onboarding session/transcript persistence. Owner: Backend."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.onboarding_session import OnboardingSession
from app.models.onboarding_turn import OnboardingTurn


def create_session(db: Session, user_id: str) -> OnboardingSession:
    session_row = OnboardingSession(user_id=user_id, status="in_progress")
    db.add(session_row)
    db.commit()
    db.refresh(session_row)
    return session_row


def get_session(db: Session, session_id: str) -> OnboardingSession | None:
    return db.get(OnboardingSession, session_id)


def get_session_for_user(
    db: Session, session_id: str, user_id: str
) -> OnboardingSession | None:
    session_row = get_session(db, session_id)
    if session_row is None or session_row.user_id != user_id:
        return None
    return session_row



def mark_completed(db: Session, session_id: str) -> None:
    session_row = db.get(OnboardingSession, session_id)
    if session_row is not None:
        session_row.status = "completed"
        db.commit()


def append_turn(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    answer_kind: str | None = None,
) -> OnboardingTurn:
    turn = OnboardingTurn(
        session_id=session_id,
        role=role,
        content=content,
        answer_kind=answer_kind if role == "user" else None,
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn


def list_turns(db: Session, session_id: str) -> list[OnboardingTurn]:
    stmt = (
        select(OnboardingTurn)
        .where(OnboardingTurn.session_id == session_id)
        .order_by(OnboardingTurn.created_at)
    )
    return list(db.scalars(stmt))
