from __future__ import annotations

import pytest

from app.core.db import SessionLocal, engine
from app.models import Base


@pytest.fixture(autouse=True, scope="session")
def _prepare_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
