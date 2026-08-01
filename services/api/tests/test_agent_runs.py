from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.di import get_llm_provider
from app.main import app
from app.models.user import User
from app.providers.llm.fake import FakeLLMProvider
from app.repositories import twin_repository
from app.workers.seed import _DECLARED_ATTRIBUTES

client = TestClient(app)


def _ensure_demo_twin(db_session) -> None:
    settings = get_settings()
    if db_session.get(User, settings.demo_user_id) is None:
        db_session.add(User(id=settings.demo_user_id, capacity=100.0))
        db_session.commit()
    if twin_repository.get_active_declared_self(db_session, settings.demo_user_id) is None:
        twin_repository.create_version(
            db_session,
            user_id=settings.demo_user_id,
            version=1,
            attributes=_DECLARED_ATTRIBUTES,
            confirmed_at=datetime.utcnow(),
        )


@pytest.fixture()
def fake_llm():
    def _use(response: dict):
        provider = FakeLLMProvider(response=response)
        app.dependency_overrides[get_llm_provider] = lambda: provider
        return provider

    yield _use
    app.dependency_overrides.pop(get_llm_provider, None)


def test_weekly_report_run(db_session, fake_llm) -> None:
    _ensure_demo_twin(db_session)
    fake_llm({"narrative": "Fearful -> attended 2 events -> Confidence marker +9."})

    resp = client.post("/api/v1/agents/runs", json={"type": "weekly_report"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "weekly_report"
    assert body["weeklyReport"]["narrative"]
    assert body["evolutionProposal"] is None


def test_evolution_run_persists_pending_proposal(db_session, fake_llm) -> None:
    _ensure_demo_twin(db_session)
    fake_llm(
        {
            "proposedAttributes": [
                {
                    "id": "entrepreneur",
                    "label": "Startup Founder",
                    "weight": 1.0,
                    "targetWeeklyPoints": 15.0,
                    "markers": [],
                }
            ],
            "citedEvidenceIds": ["evt-1", "evt-2", "evt-3"],
            "rationale": "Recent behavior suggests entrepreneurship over public speaking.",
        }
    )

    resp = client.post("/api/v1/agents/runs", json={"type": "evolution"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "evolution"
    assert body["evolutionProposal"]["status"] == "pending"
    assert body["weeklyReport"] is None
