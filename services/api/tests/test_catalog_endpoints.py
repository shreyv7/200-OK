from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.workers.seed_catalog import seed_catalog

client = TestClient(app)


def test_catalog_endpoints_return_seeded_items(db_session) -> None:
    seed_catalog(db_session)

    stories = client.get("/api/v1/catalog/stories").json()
    tools = client.get("/api/v1/catalog/tools").json()
    mentors = client.get("/api/v1/catalog/mentors").json()

    assert len(stories) >= 8
    assert len(tools) >= 10
    assert len(mentors) >= 5


def test_catalog_filters_by_bottleneck_tag(db_session) -> None:
    seed_catalog(db_session)

    resp = client.get("/api/v1/catalog/stories", params={"bottleneck": "confidence"})
    stories = resp.json()
    assert len(stories) >= 1
    assert all("confidence" in s["bottleneckTags"] for s in stories)


def test_catalog_never_returned_without_tags() -> None:
    # Structural guarantee: every seeded item has non-empty bottleneck tags,
    # so nothing can appear in a bottleneck-filtered stack without
    # justification (milestones.md M6 merge gate 3 — AIS enforces inclusion,
    # Backend guarantees the tag data exists to enforce it against).
    from app.workers.seed_catalog import _MENTORS, _STORIES, _TOOLS

    for story in _STORIES:
        assert story[-1]  # bottleneck_tags non-empty
    for tool in _TOOLS:
        assert tool[-1]
    for mentor in _MENTORS:
        assert mentor[-1]
