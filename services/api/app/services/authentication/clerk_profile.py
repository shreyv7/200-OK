"""Optional Clerk Backend API profile enrichment. Owner: Backend (A2)."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import Settings


@dataclass(frozen=True)
class ClerkProfile:
    email: str | None = None
    full_name: str | None = None
    profile_image: str | None = None


def profile_from_claims(claims: dict) -> ClerkProfile:
    email = claims.get("email")
    if isinstance(email, dict):
        email = email.get("email_address")
    full_name = claims.get("name") or claims.get("full_name")
    profile_image = claims.get("picture") or claims.get("image_url")
    return ClerkProfile(
        email=str(email) if email else None,
        full_name=str(full_name) if full_name else None,
        profile_image=str(profile_image) if profile_image else None,
    )


def fetch_clerk_user_profile(clerk_id: str, settings: Settings) -> ClerkProfile:
    """Load email/name/image from Clerk Backend API when JWT claims are sparse."""
    if not settings.clerk_secret_key:
        return ClerkProfile()

    url = f"https://api.clerk.com/v1/users/{clerk_id}"
    headers = {"Authorization": f"Bearer {settings.clerk_secret_key}"}
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError:
        return ClerkProfile()

    email: str | None = None
    primary_id = data.get("primary_email_address_id")
    for address in data.get("email_addresses") or []:
        if address.get("id") == primary_id or email is None:
            email = address.get("email_address")
            if address.get("id") == primary_id:
                break

    first = (data.get("first_name") or "").strip()
    last = (data.get("last_name") or "").strip()
    full_name = f"{first} {last}".strip() or data.get("username")

    return ClerkProfile(
        email=email,
        full_name=full_name or None,
        profile_image=data.get("image_url") or data.get("profile_image_url"),
    )


def resolve_profile(claims: dict, settings: Settings) -> ClerkProfile:
    from_claims = profile_from_claims(claims)
    if from_claims.email and from_claims.full_name:
        return from_claims

    clerk_id = str(claims.get("sub") or "")
    if not clerk_id:
        return from_claims

    from_api = fetch_clerk_user_profile(clerk_id, settings)
    return ClerkProfile(
        email=from_claims.email or from_api.email,
        full_name=from_claims.full_name or from_api.full_name,
        profile_image=from_claims.profile_image or from_api.profile_image,
    )
