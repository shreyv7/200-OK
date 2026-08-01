from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.di import get_llm_provider
from app.integrations.mcp.trellis.adapter import FixtureTrellisAdapter
from app.main import app
from app.models.user import User
from app.providers.llm.fake import FakeLLMProvider
from app.repositories import twin_repository
from app.schemas.evidence import RawMCPPayload
from app.services.evidence import service as evidence_service
from app.workers.seed import _DECLARED_ATTRIBUTES

client = TestClient(app)
_adapter = FixtureTrellisAdapter()


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


def _seed_evidence_ids(db_session, count: int = 3) -> list[str]:
    """AIA's real propose_identity_evolution only accepts citations that
    match real evidence event ids in the window — needs actual rows,
    not arbitrary strings."""
    ids = []
    for i in range(count):
        raw = RawMCPPayload(
            sourceProvider="trellis",
            rawPayload={
                "userId": get_settings().demo_user_id,
                "type": "mission_completed",
                "timestamp": (datetime.utcnow() - timedelta(minutes=i + 1)).isoformat(),
                "units": 1.0,
            },
        )
        event = _adapter.normalize(raw)
        request = evidence_service.request_from_event(event)
        row, _created = evidence_service.ingest(db_session, request)
        ids.append(row.id)
    return ids


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
    fake_llm(
        {
            "narrative": "Fearful -> attended 2 events -> Confidence marker +9.",
            "highlights": ["Attended 2 speaking events"],
        }
    )

    resp = client.post("/api/v1/agents/runs", json={"type": "weekly_report"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "weekly_report"
    assert body["weeklyReport"]["narrative"]
    assert body["evolutionProposal"] is None


def test_evolution_run_persists_pending_proposal(db_session, fake_llm) -> None:
    _ensure_demo_twin(db_session)
    evidence_ids = _seed_evidence_ids(db_session)
    fake_llm(
        {
            "narrative": "Recent behavior suggests entrepreneurship over public speaking.",
            "proposedChanges": [
                {
                    "action": "add",
                    "attributeId": "entrepreneur",
                    "attributeLabel": "Startup Founder",
                    "newWeight": 0.3,
                    "reason": "Shipped multiple missions this week.",
                    "evidenceIds": evidence_ids,
                }
            ],
        }
    )

    resp = client.post("/api/v1/agents/runs", json={"type": "evolution"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "evolution"
    assert body["evolutionProposal"] is not None
    assert body["evolutionProposal"]["proposedChanges"][0]["action"] == "add"
    assert body["weeklyReport"] is None
