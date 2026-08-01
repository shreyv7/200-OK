"""Clerk JWKS session-token verification. Owner: Backend (A1)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

from app.core.config import Settings


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True)


def clear_jwks_client_cache() -> None:
    """Reset cached JWKS clients (tests / key rotation)."""
    _jwks_client.cache_clear()


def verify_clerk_session_token(token: str, settings: Settings) -> dict[str, Any]:
    """Verify Clerk session JWT via JWKS; return claims (must include ``sub``).

    Checks signature (RS256), issuer, expiry, optional audience, and authorized
    party (``azp``) when configured.
    """
    if not settings.clerk_jwks_url or not settings.clerk_issuer:
        raise ValueError("Clerk JWKS URL and issuer must be configured")

    client = _jwks_client(settings.clerk_jwks_url)
    signing_key = client.get_signing_key_from_jwt(token)

    decode_kwargs: dict[str, Any] = {
        "algorithms": ["RS256"],
        "issuer": settings.clerk_issuer,
        "options": {
            "require": ["exp", "iss", "sub"],
            "verify_aud": bool(settings.clerk_audience),
        },
    }
    if settings.clerk_audience:
        decode_kwargs["audience"] = settings.clerk_audience

    claims = jwt.decode(token, signing_key.key, **decode_kwargs)

    authorized = settings.clerk_authorized_party_list
    azp = claims.get("azp")
    if authorized and azp and azp not in authorized:
        raise jwt.InvalidTokenError(f"Unauthorized party: {azp}")

    return claims
