from __future__ import annotations

from datetime import timedelta

from app.providers.search.base import Document
from app.repositories import resource_cache_repository


def test_store_then_get_fresh_round_trip(db_session) -> None:
    query = "unique test query for resource cache"
    docs = [Document(title="T", url="https://example.com/t", extract="E", source="tavily")]

    assert resource_cache_repository.get_fresh(db_session, query) is None

    resource_cache_repository.store(db_session, query, docs, badge="Live web")
    cached = resource_cache_repository.get_fresh(db_session, query)

    assert cached is not None
    assert cached[0].title == "T"


def test_get_fresh_respects_ttl(db_session) -> None:
    query = "another unique query for ttl test"
    docs = [Document(title="T2", url="https://example.com/t2", extract="E2", source="tavily")]
    resource_cache_repository.store(db_session, query, docs, badge="Live web")

    # A zero/negative TTL means "nothing is fresh".
    assert resource_cache_repository.get_fresh(db_session, query, ttl=timedelta(seconds=-1)) is None
