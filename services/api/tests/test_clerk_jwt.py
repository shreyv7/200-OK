"""A1: Clerk JWKS verification replaces the 501 stub."""

from __future__ import annotations

import time
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select

from app.core.config import Settings
from app.core.security import get_current_user_id
from app.models.user import User
from app.services.authentication.clerk import (
    clear_jwks_client_cache,
    verify_clerk_session_token,
)


ISSUER = "https://example.clerk.accounts.dev"
JWKS_URL = "https://example.clerk.accounts.dev/.well-known/jwks.json"
AUDIENCE = "trellis-api"
AZP = "http://localhost:5173"


@pytest.fixture()
def rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


@pytest.fixture()
def patch_jwks(monkeypatch: pytest.MonkeyPatch, rsa_keypair):
    private_key, public_key = rsa_keypair

    class _Key:
        key = public_key

    class _Client:
        def get_signing_key_from_jwt(self, _token: str) -> _Key:
            return _Key()

    clear_jwks_client_cache()
    monkeypatch.setattr(
        "app.services.authentication.clerk._jwks_client",
        lambda _url: _Client(),
    )
    return private_key


def _settings(**overrides: Any) -> Settings:
    base = {
        "env": "local",
        "auth_bypass": False,
        "clerk_jwks_url": JWKS_URL,
        "clerk_issuer": ISSUER,
        "clerk_audience": AUDIENCE,
        "clerk_authorized_parties": AZP,
    }
    base.update(overrides)
    return Settings(**base)


def _mint(private_key, *, sub: str = "user_clerk_abc", **extra: Any) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "azp": AZP,
        "iat": now,
        "exp": now + 300,
        **extra,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def test_verify_accepts_valid_token(patch_jwks) -> None:
    token = _mint(patch_jwks)
    claims = verify_clerk_session_token(token, _settings())
    assert claims["sub"] == "user_clerk_abc"


def test_verify_rejects_wrong_issuer(patch_jwks) -> None:
    token = _mint(patch_jwks, iss="https://evil.example")
    with pytest.raises(jwt.InvalidIssuerError):
        verify_clerk_session_token(token, _settings())


def test_verify_rejects_wrong_audience(patch_jwks) -> None:
    token = _mint(patch_jwks, aud="other-audience")
    with pytest.raises(jwt.InvalidAudienceError):
        verify_clerk_session_token(token, _settings())


def test_verify_rejects_unauthorized_azp(patch_jwks) -> None:
    token = _mint(patch_jwks, azp="https://evil.example")
    with pytest.raises(jwt.InvalidTokenError, match="Unauthorized party"):
        verify_clerk_session_token(token, _settings())


def test_verify_requires_jwks_config(patch_jwks) -> None:
    token = _mint(patch_jwks)
    with pytest.raises(ValueError, match="JWKS URL and issuer"):
        verify_clerk_session_token(token, _settings(clerk_jwks_url=None, clerk_issuer=None))


def test_get_current_user_id_bypass_local_only() -> None:
    settings = Settings(env="local", auth_bypass=True, demo_user_id="demo-user-aarav")
    assert (
        get_current_user_id(authorization=None, settings=settings, db=None)  # type: ignore[arg-type]
        == "demo-user-aarav"
    )


def test_get_current_user_id_ignores_bypass_outside_local() -> None:
    settings = Settings(env="prod", auth_bypass=True)
    with pytest.raises(Exception) as excinfo:
        get_current_user_id(authorization=None, settings=settings, db=None)  # type: ignore[arg-type]
    assert excinfo.value.status_code == 401


def test_maps_sub_to_internal_user_id(patch_jwks, db_session) -> None:
    token = _mint(patch_jwks, sub="clerk_sub_integration")
    settings = _settings(auth_bypass=False)

    user_id = get_current_user_id(
        authorization=f"Bearer {token}",
        settings=settings,
        db=db_session,
    )
    assert user_id
    row = db_session.scalar(select(User).where(User.clerk_subject == "clerk_sub_integration"))
    assert row is not None
    assert row.id == user_id

    again = get_current_user_id(
        authorization=f"Bearer {token}",
        settings=settings,
        db=db_session,
    )
    assert again == user_id


def test_invalid_token_returns_401(patch_jwks, db_session) -> None:
    settings = _settings(auth_bypass=False)
    with pytest.raises(Exception) as excinfo:
        get_current_user_id(
            authorization="Bearer not-a-jwt",
            settings=settings,
            db=db_session,
        )
    assert excinfo.value.status_code == 401


def test_missing_bearer_returns_401(db_session) -> None:
    settings = _settings(auth_bypass=False)
    with pytest.raises(Exception) as excinfo:
        get_current_user_id(authorization=None, settings=settings, db=db_session)
    assert excinfo.value.status_code == 401
