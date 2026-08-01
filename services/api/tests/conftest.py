from __future__ import annotations

import os

import pytest

# Force local bypass for the suite so tests never need live Clerk credentials.
# Must be set before app modules that read Settings at import time.
os.environ.setdefault("ENV", "local")
os.environ["AUTH_BYPASS"] = "true"

from app.core.db import SessionLocal, engine
from app.models import Base


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


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
