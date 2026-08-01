"""A2: Clerk sub → User upsert with email / last_login_at."""

from __future__ import annotations

import time
from datetime import datetime

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select

from app.core.config import Settings
from app.core.security import get_current_user
from app.models.user import User
from app.repositories import user_repository
from app.services.authentication.clerk import clear_jwks_client_cache


ISSUER = "https://example.clerk.accounts.dev"
JWKS_URL = "https://example.clerk.accounts.dev/.well-known/jwks.json"
AZP = "http://localhost:5173"


@pytest.fixture()
def rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


@pytest.fixture()
def patch_jwks(monkeypatch: pytest.MonkeyPatch, rsa_keypair):
    private_key, public_key = rsa_keypair
    clear_jwks_client_cache()
    monkeypatch.setattr(
        "app.services.authentication.clerk._signing_key_for_token",
        lambda _token, _url: public_key,
    )
    return private_key


def _settings(**overrides) -> Settings:
    base = {
        "env": "local",
        "auth_bypass": False,
        "clerk_jwks_url": JWKS_URL,
        "clerk_issuer": ISSUER,
        "clerk_authorized_parties": AZP,
        "clerk_secret_key": None,
    }
    base.update(overrides)
    return Settings(**base)


def _mint(private_key, *, sub: str = "user_clerk_a2", **extra) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "iss": ISSUER,
        "azp": AZP,
        "email": "shrey@example.com",
        "name": "Shrey V",
        "picture": "https://img.example/a.png",
        "iat": now,
        "exp": now + 300,
        **extra,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def test_upsert_creates_user_with_profile_and_last_login(db_session) -> None:
    user, created = user_repository.upsert_from_clerk(
        db_session,
        clerk_subject="clerk_sub_1",
        email="a@example.com",
        full_name="Ada",
        profile_image="https://img/a",
    )
    assert created is True
    assert user.email == "a@example.com"
    assert user.full_name == "Ada"
    assert user.last_login_at is not None

    again, created2 = user_repository.upsert_from_clerk(
        db_session,
        clerk_subject="clerk_sub_1",
        email="a@example.com",
        full_name="Ada Lovelace",
    )
    assert created2 is False
    assert again.id == user.id
    assert again.full_name == "Ada Lovelace"
    assert again.last_login_at is not None


def test_get_current_user_provisions_from_jwt_claims(patch_jwks, db_session) -> None:
    token = _mint(patch_jwks, sub="clerk_live_a2")
    user = get_current_user(
        authorization=f"Bearer {token}",
        settings=_settings(),
        db=db_session,
    )
    assert user.clerk_subject == "clerk_live_a2"
    assert user.email == "shrey@example.com"
    assert user.full_name == "Shrey V"
    assert user.profile_image == "https://img.example/a.png"
    assert isinstance(user.last_login_at, datetime)

    row = db_session.scalar(select(User).where(User.clerk_subject == "clerk_live_a2"))
    assert row is not None
    assert row.id == user.id


def test_me_returns_provisioned_fields(patch_jwks, db_session) -> None:
    from app.api.me import get_me

    token = _mint(patch_jwks, sub="clerk_me_a2")
    user = get_current_user(
        authorization=f"Bearer {token}",
        settings=_settings(),
        db=db_session,
    )
    body = get_me(user=user)
    assert body.email == "shrey@example.com"
    assert body.full_name == "Shrey V"
    assert body.clerk_id == "clerk_me_a2"


def test_seed_refuses_without_allow_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.workers import seed

    monkeypatch.setenv("ALLOW_DEMO_SEED", "false")
    # Settings reads env at construction
    with pytest.raises(SystemExit, match="ALLOW_DEMO_SEED"):
        # Force fresh settings inside seed.main
        monkeypatch.setattr(
            "app.workers.seed.get_settings",
            lambda: Settings(allow_demo_seed=False),
        )
        seed.main()


def test_prewarm_refuses_without_user_id(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.workers import prewarm

    monkeypatch.setattr(
        "app.workers.prewarm.get_settings",
        lambda: Settings(prewarm_user_id=None),
    )
    with pytest.raises(SystemExit, match="PREWARM_USER_ID"):
        prewarm.main()
