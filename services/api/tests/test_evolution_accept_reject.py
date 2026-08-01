from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from app.core.di import get_current_user_id
from app.main import app
from app.repositories import evolution_repository, twin_repository
from app.schemas.evolution import IdentityEvolutionProposal, ProposedChange
from app.schemas.identity import IdentityAttribute
from tests.conftest import ensure_user


client = TestClient(app)


def _make_proposal(user_id: str, version: int, changes: list[ProposedChange]) -> IdentityEvolutionProposal:
    return IdentityEvolutionProposal(
        proposalId=f"prop-{user_id}",
        userId=user_id,
        declaredSelfVersion=version,
        proposedChanges=changes,
        supportingEvidenceIds=["e1", "e2", "e3"],
        narrative="test rationale",
        generatedAt=datetime.utcnow(),
    )


def test_accept_applies_diff_not_a_flat_replace(db_session) -> None:
    # Isolated user_id — accept always writes for the AUTH_BYPASS demo user
    # via the API, so this is tested at the repository/service level to
    # avoid mutating the shared demo user's identity that other test files
    # (e.g. M2's test_identity_endpoint.py) depend on.
    user_id = "user-evolution-accept"
    ensure_user(db_session, user_id)
    twin_repository.create_version(
        db_session,
        user_id=user_id,
        version=1,
        attributes=[
            IdentityAttribute(id="a", label="A", weight=0.5, targetWeeklyPoints=15.0, markers=[]),
            IdentityAttribute(id="b", label="B", weight=0.5, targetWeeklyPoints=15.0, markers=[]),
        ],
        confirmed_at=None,
    )
    twin_repository.confirm_draft(db_session, user_id)

    proposal = evolution_repository.create(
        db_session,
        _make_proposal(
            user_id,
            version=1,
            changes=[
                ProposedChange(
                    action="add",
                    attributeId="c",
                    attributeLabel="C",
                    newWeight=0.3,
                    reason="test",
                    evidenceIds=["e1", "e2", "e3"],
                ),
                ProposedChange(
                    action="remove",
                    attributeId="b",
                    attributeLabel="B",
                    reason="test",
                    evidenceIds=["e1", "e2", "e3"],
                ),
            ],
        ),
    )

    from app.services.identity.agent_runs import apply_proposed_changes

    current = twin_repository.get_active_declared_self(db_session, user_id)
    merged = apply_proposed_changes(current.attributes, proposal.proposedChanges)
    new_twin = twin_repository.create_confirmed_version(db_session, user_id, merged)

    ids = {a.id for a in new_twin.attributes}
    assert ids == {"a", "c"}  # "b" removed, "a" untouched (not a flat replace), "c" added
    assert new_twin.version == 2


def test_reject_leaves_identity_unchanged(db_session) -> None:
    user_id = "user-evolution-reject"
    ensure_user(db_session, user_id)
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
        _make_proposal(
            user_id,
            version=1,
            changes=[
                ProposedChange(
                    action="add",
                    attributeId="c",
                    attributeLabel="C",
                    reason="test",
                    evidenceIds=["e1", "e2", "e3"],
                )
            ],
        ),
    )

    app.dependency_overrides[get_current_user_id] = lambda: user_id
    try:
        resp = client.post(f"/api/v1/identity/evolution/{proposal.proposalId}/reject")
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    active = twin_repository.get_active_declared_self(db_session, user_id)
    assert active.version == 1
    assert active.attributes[0].id == "a"
