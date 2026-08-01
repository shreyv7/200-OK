"""A3: two-user isolation — zero cross-read / cross-write contamination."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.core.di import get_current_user_id
from app.main import app
from app.repositories import (
    evolution_repository,
    ledger_repository,
    onboarding_repository,
    twin_repository,
)
from app.schemas.evolution import IdentityEvolutionProposal, ProposedChange
from app.schemas.identity import IdentityAttribute
from app.services.identity.scoring.constants import DISMISSAL_FAILURE_THRESHOLD
from tests.conftest import ensure_user

client = TestClient(app)

USER_A = "user-isolation-a"
USER_B = "user-isolation-b"


def _as_user(user_id: str):
    app.dependency_overrides[get_current_user_id] = lambda: user_id


def _clear_user_override() -> None:
    app.dependency_overrides.pop(get_current_user_id, None)


def _attrs(label_suffix: str) -> list[IdentityAttribute]:
    return [
        IdentityAttribute(
            id=f"attr_{label_suffix}",
            label=f"Attr {label_suffix}",
            weight=1.0,
            targetWeeklyPoints=15.0,
            markers=[],
        )
    ]


def _seed_user(db_session, user_id: str, label: str) -> None:
    ensure_user(db_session, user_id)
    twin_repository.create_version(
        db_session,
        user_id=user_id,
        version=1,
        attributes=_attrs(label),
        confirmed_at=datetime.utcnow(),
    )


def test_evidence_and_identity_are_isolated(db_session) -> None:
    _seed_user(db_session, USER_A, "a")
    _seed_user(db_session, USER_B, "b")

    try:
        _as_user(USER_A)
        post_a = client.post(
            "/api/v1/evidence",
            json={
                "timestamp": datetime.utcnow().isoformat(),
                "source": "trellis",
                "type": "isolation_a_event",
                "category": "creation",
                "value": 1.0,
                "baseWeight": 3.0,
                "metadata": {"owner": "a"},
                "simulated": True,
            },
        )
        assert post_a.status_code == 201
        assert post_a.json()["userId"] == USER_A

        _as_user(USER_B)
        post_b = client.post(
            "/api/v1/evidence",
            json={
                "timestamp": datetime.utcnow().isoformat(),
                "source": "trellis",
                "type": "isolation_b_event",
                "category": "creation",
                "value": 1.0,
                "baseWeight": 3.0,
                "metadata": {"owner": "b"},
                "simulated": True,
            },
        )
        assert post_b.status_code == 201
        assert post_b.json()["userId"] == USER_B

        _as_user(USER_A)
        events_a = client.get("/api/v1/evidence").json()
        types_a = {e["type"] for e in events_a}
        assert "isolation_a_event" in types_a
        assert "isolation_b_event" not in types_a
        assert all(e["userId"] == USER_A for e in events_a)

        identity_a = client.get("/api/v1/identity").json()
        assert identity_a["attributes"][0]["id"] == "attr_a"

        _as_user(USER_B)
        events_b = client.get("/api/v1/evidence").json()
        types_b = {e["type"] for e in events_b}
        assert "isolation_b_event" in types_b
        assert "isolation_a_event" not in types_b
        identity_b = client.get("/api/v1/identity").json()
        assert identity_b["attributes"][0]["id"] == "attr_b"
    finally:
        _clear_user_override()


def test_evolution_accept_reject_cannot_touch_other_user(db_session) -> None:
    _seed_user(db_session, USER_A, "a")
    _seed_user(db_session, USER_B, "b")

    proposal = evolution_repository.create(
        db_session,
        IdentityEvolutionProposal(
            proposalId="prop-isolation-b",
            userId=USER_B,
            declaredSelfVersion=1,
            proposedChanges=[
                ProposedChange(
                    action="add",
                    attributeId="stolen",
                    attributeLabel="Stolen",
                    reason="idor",
                    evidenceIds=["e1", "e2", "e3"],
                )
            ],
            supportingEvidenceIds=["e1", "e2", "e3"],
            narrative="should not be touchable by A",
            generatedAt=datetime.utcnow(),
        ),
    )

    try:
        _as_user(USER_A)
        accept = client.post(f"/api/v1/identity/evolution/{proposal.proposalId}/accept")
        reject = client.post(f"/api/v1/identity/evolution/{proposal.proposalId}/reject")
        assert accept.status_code == 404
        assert reject.status_code == 404

        found = evolution_repository.get(db_session, proposal.proposalId)
        assert found is not None
        assert found[0].status == "pending"

        twin_a = twin_repository.get_active_declared_self(db_session, USER_A)
        assert twin_a is not None
        assert all(a.id != "stolen" for a in twin_a.attributes)

        twin_b = twin_repository.get_active_declared_self(db_session, USER_B)
        assert twin_b is not None
        assert twin_b.version == 1
    finally:
        _clear_user_override()


def test_onboarding_session_cannot_be_hijacked(db_session) -> None:
    ensure_user(db_session, USER_A)
    ensure_user(db_session, USER_B)

    session_b = onboarding_repository.create_session(db_session, USER_B)
    onboarding_repository.append_turn(db_session, session_b.id, "assistant", "Q1 for B")

    try:
        _as_user(USER_A)
        resp = client.post(
            "/api/v1/identity/onboarding",
            json={"sessionId": session_b.id, "message": "hijack attempt"},
        )
        assert resp.status_code == 404

        turns = onboarding_repository.list_turns(db_session, session_b.id)
        assert len(turns) == 1
        assert turns[0].role == "assistant"
    finally:
        _clear_user_override()


def test_ledger_dismissal_threshold_is_per_user(db_session) -> None:
    ensure_user(db_session, USER_A)
    ensure_user(db_session, USER_B)
    family = "hyp-family-shared"

    # B already has enough dismissals to trip the threshold alone.
    for i in range(DISMISSAL_FAILURE_THRESHOLD):
        ledger_repository.record(
            db_session,
            user_id=USER_B,
            hypothesis_id=f"hyp-b-{i}",
            hypothesis_family=family,
            action="dismissed",
            verdict="pending",
        )

    try:
        _as_user(USER_A)
        # A's first dismissal for the same family must NOT inherit B's count.
        resp = client.post(
            "/api/v1/ledger/record",
            json={
                "hypothesisId": "hyp-a-1",
                "hypothesisFamily": family,
                "action": "dismissed",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["userId"] == USER_A
        assert body["verdict"] == "pending"
        assert body["unlearningTriggered"] is False

        ledger_a = client.get("/api/v1/ledger").json()
        assert all(e["userId"] == USER_A for e in ledger_a)
        assert all(e["hypothesisId"].startswith("hyp-a") for e in ledger_a)

        _as_user(USER_B)
        ledger_b = client.get("/api/v1/ledger").json()
        assert all(e["userId"] == USER_B for e in ledger_b)
        assert len(ledger_b) >= DISMISSAL_FAILURE_THRESHOLD
    finally:
        _clear_user_override()


def test_stale_client_user_id_field_is_ignored_on_evidence(db_session) -> None:
    """Extra body userId must not attribute the row (field removed; extras ignored)."""
    ensure_user(db_session, USER_A)
    ensure_user(db_session, USER_B)

    try:
        _as_user(USER_A)
        resp = client.post(
            "/api/v1/evidence",
            json={
                "userId": USER_B,
                "timestamp": (datetime.utcnow() - timedelta(seconds=1)).isoformat(),
                "source": "trellis",
                "type": "spoof_attempt",
                "category": "creation",
                "value": 1.0,
                "baseWeight": 3.0,
                "metadata": {},
                "simulated": True,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["userId"] == USER_A

        _as_user(USER_B)
        events_b = client.get("/api/v1/evidence").json()
        assert all(e["type"] != "spoof_attempt" for e in events_b)
    finally:
        _clear_user_override()
