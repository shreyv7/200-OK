from __future__ import annotations

from app.models.catalog import GrowthStoryModel, MentorModel, ToolModel
from app.workers.seed_catalog import seed_catalog


def _clear_catalog(db_session) -> None:
    db_session.query(GrowthStoryModel).delete()
    db_session.query(ToolModel).delete()
    db_session.query(MentorModel).delete()
    db_session.commit()


def test_seed_catalog_is_idempotent(db_session) -> None:
    _clear_catalog(db_session)
    first = seed_catalog(db_session)
    assert first == (8, 10, 5)

    second = seed_catalog(db_session)
    assert second == (0, 0, 0)
