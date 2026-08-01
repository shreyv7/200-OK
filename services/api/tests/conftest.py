from __future__ import annotations

import os

import pytest

# Isolate the suite from the local app DB. Must be set before app.core.db imports
# — otherwise pytest drop_all wipes the running Trellis schema.
os.environ.setdefault("ENV", "local")
os.environ["AUTH_BYPASS"] = "true"
os.environ["SEARCH_PROVIDER"] = "fake"
os.environ["LLM_PROVIDER"] = "fake"
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://trellis:trellis@localhost:5432/trellis_test"
)

from app.core.db import SessionLocal, engine
from app.models import Base
from app.models.user import User


@pytest.fixture(autouse=True, scope="session")
def _prepare_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _force_auth_bypass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "local")
    monkeypatch.setenv("AUTH_BYPASS", "true")
    monkeypatch.setenv("SEARCH_PROVIDER", "fake")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://trellis:trellis@localhost:5432/trellis_test",
    )


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def ensure_user(db, user_id: str) -> User:
    """Insert a users row when tests write FK-scoped tables directly."""
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id, capacity=100.0)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
