"""Clerk JWKS session-token verification. Owner: Backend (A1)."""

from __future__ import annotations

import time
from functools import lru_cache
from typing import Any

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm

from app.core.config import Settings

# kid → (pem_or_key, fetched_at)
_KEY_CACHE: dict[str, tuple[Any, float]] = {}
_KEY_TTL_SECONDS = 300.0


def clear_jwks_client_cache() -> None:
    """Reset cached JWKS keys (tests / key rotation)."""
    _KEY_CACHE.clear()
    _fetch_jwks.cache_clear()


@lru_cache(maxsize=4)
def _fetch_jwks(jwks_url: str) -> dict[str, Any]:
    # httpx uses certifi by default — more reliable than urllib on macOS Python.
    response = httpx.get(jwks_url, timeout=5.0)
    response.raise_for_status()
    return response.json()


def _signing_key_for_token(token: str, jwks_url: str) -> Any:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
        raise jwt.InvalidTokenError("JWT missing kid header")

    cached = _KEY_CACHE.get(kid)
    now = time.time()
    if cached and now - cached[1] < _KEY_TTL_SECONDS:
        return cached[0]

    jwks = _fetch_jwks(jwks_url)
    # Bust lru after TTL window so rotated keys are picked up.
    if cached and now - cached[1] >= _KEY_TTL_SECONDS:
        _fetch_jwks.cache_clear()
        jwks = _fetch_jwks(jwks_url)

    for jwk in jwks.get("keys") or []:
        if jwk.get("kid") != kid:
            continue
        key = RSAAlgorithm.from_jwk(jwk)
        _KEY_CACHE[kid] = (key, now)
        return key

    # kid miss — refresh once in case of rotation
    _fetch_jwks.cache_clear()
    jwks = _fetch_jwks(jwks_url)
    for jwk in jwks.get("keys") or []:
        if jwk.get("kid") != kid:
            continue
        key = RSAAlgorithm.from_jwk(jwk)
        _KEY_CACHE[kid] = (key, now)
        return key

    raise jwt.InvalidTokenError(f"Unable to find signing key for kid={kid}")


def verify_clerk_session_token(token: str, settings: Settings) -> dict[str, Any]:
    """Verify Clerk session JWT via JWKS; return claims (must include ``sub``).

    Checks signature (RS256), issuer, expiry, optional audience, and authorized
    party (``azp``) when configured.
    """
    if not settings.clerk_jwks_url or not settings.clerk_issuer:
        raise ValueError("Clerk JWKS URL and issuer must be configured")

    signing_key = _signing_key_for_token(token, settings.clerk_jwks_url)

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

    claims = jwt.decode(token, signing_key, **decode_kwargs)

    # Allow frontend origins plus the Clerk Frontend API host (some session
    # tokens set azp to the issuer rather than the browser origin).
    authorized = set(settings.clerk_authorized_party_list)
    if settings.clerk_issuer:
        authorized.add(settings.clerk_issuer.rstrip("/"))
    azp = claims.get("azp")
    if authorized and azp and azp not in authorized:
        raise jwt.InvalidTokenError(f"Unauthorized party: {azp}")

    return claims
