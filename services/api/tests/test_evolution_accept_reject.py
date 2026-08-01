from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.repositories import evolution_repository, twin_repository
from app.schemas.identity import IdentityAttribute

client = TestClient(app)


def test_accept_creates_new_confirmed_version_gap_uses_it(db_session) -> None:
    # Isolated user_id — accept always writes for the AUTH_BYPASS demo user
    # via the API, so the "new version" assertion is tested at the
    # repository level to avoid mutating the shared demo user's identity
    # that other test files (e.g. M2's test_identity_endpoint.py) depend on.
    user_id = "user-evolution-accept"
    twin_repository.create_version(
        db_session,
        user_id=user_id,
        version=1,
        attributes=[
            IdentityAttribute(id="a", label="A", weight=1.0, targetWeeklyPoints=15.0, markers=[])
        ],
        confirmed_at=None,
    )
    twin_repository.confirm_draft(db_session, user_id)
    before = twin_repository.get_active_declared_self(db_session, user_id)
    assert before.version == 1

    proposal = evolution_repository.create(
        db_session,
        user_id=user_id,
        proposed_attributes=[
            IdentityAttribute(id="b", label="B", weight=1.0, targetWeeklyPoints=15.0, markers=[])
        ],
        cited_evidence_ids=["e1", "e2", "e3"],
        rationale="test rationale",
    )

    new_twin = twin_repository.create_confirmed_version(db_session, user_id, proposal.proposedAttributes)
    assert new_twin.version == 2
    active = twin_repository.get_active_declared_self(db_session, user_id)
    assert active.version == 2
    assert active.attributes[0].id == "b"


def test_reject_leaves_identity_unchanged(db_session) -> None:
    user_id = "user-evolution-reject"
    twin_repository.create_version(
        db_session,
        user_id=user_id,
        version=1,
        attributes=[
            IdentityAttribute(id="a", label="A", weight=1.0, targetWeeklyPoints=15.0, markers=[])
        ],
        confirmed_at=None,
    )
    twin_repository.confirm_draft(db_session, user_id)

    proposal = evolution_repository.create(
        db_session,
        user_id=user_id,
        proposed_attributes=[
            IdentityAttribute(id="c", label="C", weight=1.0, targetWeeklyPoints=15.0, markers=[])
        ],
        cited_evidence_ids=["e1", "e2", "e3"],
        rationale="test rationale",
    )

    resp = client.post(f"/api/v1/identity/evolution/{proposal.id}/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    # Rejection must not have touched the identity at all — still v1, "a".
    active = twin_repository.get_active_declared_self(db_session, user_id)
    assert active.version == 1
    assert active.attributes[0].id == "a"
