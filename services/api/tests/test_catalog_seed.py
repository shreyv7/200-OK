from __future__ import annotations

from app.workers.seed_catalog import seed_catalog


def test_seed_catalog_is_idempotent(db_session) -> None:
    first = seed_catalog(db_session)
    assert first == (8, 10, 5)

    second = seed_catalog(db_session)
    assert second == (0, 0, 0)
