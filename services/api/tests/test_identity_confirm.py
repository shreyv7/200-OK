from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import twin_repository
from app.schemas.identity import IdentityAttribute

client = TestClient(app)

_VALID_ATTRIBUTES = [
    {
        "id": "public_speaker",
        "label": "Confident Public Speaker",
        "weight": 0.5,
        "targetWeeklyPoints": 15.0,
        "markers": [],
    },
    {
        "id": "builder",
        "label": "Builder Who Ships Projects",
        "weight": 0.5,
        "targetWeeklyPoints": 15.0,
        "markers": [],
    },
]

_UNBALANCED_ATTRIBUTES = [
    {**_VALID_ATTRIBUTES[0], "weight": 0.9},
    {**_VALID_ATTRIBUTES[1], "weight": 0.9},
]


def test_patch_without_confirm_only_updates_draft() -> None:
    resp = client.patch(
        "/api/v1/identity", json={"attributes": _VALID_ATTRIBUTES, "confirm": False}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmedAt"] is None


def test_patch_confirm_rejects_unbalanced_weights() -> None:
    resp = client.patch(
        "/api/v1/identity", json={"attributes": _UNBALANCED_ATTRIBUTES, "confirm": True}
    )
    assert resp.status_code == 422


def test_confirm_draft_promotes_to_active_with_balanced_weights(db_session) -> None:
    # Uses an isolated user_id (not the shared AUTH_BYPASS demo user) so this
    # doesn't change what other tests' `GET /identity` sees for the demo user.
    user_id = "user-confirm-isolated"
    attributes = [IdentityAttribute.model_validate(a) for a in _VALID_ATTRIBUTES]

    twin_repository.upsert_draft(db_session, user_id, attributes)
    confirmed = twin_repository.confirm_draft(db_session, user_id)

    assert confirmed.confirmedAt is not None
    assert twin_repository.get_active_declared_self(db_session, user_id) is not None
    assert twin_repository.get_draft(db_session, user_id) is None  # no longer a draft


def test_confirm_draft_raises_on_unbalanced_weights(db_session) -> None:
    from app.repositories.twin_repository import WeightSumError

    user_id = "user-confirm-unbalanced"
    attributes = [IdentityAttribute.model_validate(a) for a in _UNBALANCED_ATTRIBUTES]
    twin_repository.upsert_draft(db_session, user_id, attributes)

    with pytest.raises(WeightSumError):
        twin_repository.confirm_draft(db_session, user_id)
