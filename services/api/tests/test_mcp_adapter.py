from __future__ import annotations

from datetime import datetime

from app.integrations.mcp.github.adapter import FixtureGithubAdapter
from app.integrations.mcp.trellis.adapter import FixtureTrellisAdapter
from app.schemas.evidence import RawMCPPayload
from app.services.evidence import service as evidence_service


def test_github_adapter_normalizes_commit_fixture() -> None:
    adapter = FixtureGithubAdapter()
    raw = RawMCPPayload(
        sourceProvider="github",
        rawPayload={
            "userId": "u1",
            "timestamp": datetime.utcnow().isoformat(),
            "sha": "abc123",
            "message": "test commit",
        },
    )
    event = adapter.normalize(raw)

    assert event.source == "github"
    assert event.category == "creation"
    assert event.simulated is True
    assert event.baseWeight == 4.0


def test_trellis_adapter_normalizes_focus_drift() -> None:
    adapter = FixtureTrellisAdapter()
    raw = RawMCPPayload(
        sourceProvider="trellis",
        rawPayload={
            "userId": "u1",
            "type": "focus_drift",
            "timestamp": datetime.utcnow().isoformat(),
            "units": 2.0,
        },
    )
    event = adapter.normalize(raw)

    assert event.category == "focus_drift"
    assert event.baseWeight == -2.0
    assert event.value == 2.0


def test_adapter_output_flows_through_ingest_pipeline(db_session) -> None:
    adapter = FixtureGithubAdapter()
    raw = RawMCPPayload(
        sourceProvider="github",
        rawPayload={
            "userId": "u-adapter-pipeline",
            "timestamp": datetime.utcnow().isoformat(),
            "sha": "def456",
            "message": "pipeline test",
        },
    )
    event = adapter.normalize(raw)
    request = evidence_service.request_from_event(event)

    row, created = evidence_service.ingest(db_session, request)

    assert created is True
    assert row.source == "github"
    assert row.simulated is True
