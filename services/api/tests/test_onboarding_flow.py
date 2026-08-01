from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.di import get_llm_provider
from app.main import app
from app.providers.llm.fake import FakeLLMProvider
from app.services.identity.onboarding_orchestration import FIXED_ONBOARDING_TOPICS

client = TestClient(app)

_FAKE_EXTRACTION_RESPONSE = {
    "attributes": [
        {
            "id": "public_speaker",
            "label": "Confident Public Speaker",
            "weight": 0.5,
            "targetWeeklyPoints": 15.0,
            "markers": [{"id": "speaks_publicly", "label": "Speaks in front of others"}],
        },
        {
            "id": "builder",
            "label": "Builder Who Ships Projects",
            "weight": 0.5,
            "targetWeeklyPoints": 15.0,
            "markers": [{"id": "ships_code", "label": "Commits and publishes code"}],
        },
    ]
}


@pytest.fixture()
def fake_llm():
    provider = FakeLLMProvider(response=_FAKE_EXTRACTION_RESPONSE)
    app.dependency_overrides[get_llm_provider] = lambda: provider
    yield provider
    app.dependency_overrides.pop(get_llm_provider, None)


def test_onboarding_starts_with_first_fixed_question() -> None:
    resp = client.post("/api/v1/identity/onboarding", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["nextQuestion"] == FIXED_ONBOARDING_TOPICS[0]
    assert body["done"] is False
    assert body["draft"] is None


def test_full_onboarding_flow_produces_draft(fake_llm) -> None:
    start = client.post("/api/v1/identity/onboarding", json={})
    session_id = start.json()["sessionId"]

    answers = [
        "I want to become a confident public speaker and a builder.",
        "Because I want to ship real projects and share them.",
        "I watch tutorials but rarely publish anything.",
        "Fear of being judged when I put my work out there.",
        "About 5 hours a week.",
    ]

    last_response = None
    for answer in answers:
        last_response = client.post(
            "/api/v1/identity/onboarding",
            json={"sessionId": session_id, "message": answer},
        )
        assert last_response.status_code == 200

    body = last_response.json()
    assert body["done"] is True
    assert body["draft"] is not None
    ids = {a["id"] for a in body["draft"]["attributes"]}
    assert ids == {"public_speaker", "builder"}
    assert fake_llm.calls  # the extraction call actually happened


def test_unknown_session_id_is_404() -> None:
    resp = client.post(
        "/api/v1/identity/onboarding",
        json={"sessionId": "does-not-exist", "message": "hi"},
    )
    assert resp.status_code == 404
