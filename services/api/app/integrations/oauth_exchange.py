"""Provider-specific OAuth 2.0 token exchange and refresh services. Owner: Person D.

Handles code -> token exchange and refresh_token -> access_token exchange via HTTP requests.
Designed to be mocked cleanly in tests without real OAuth client credentials.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class TokenResponse:
    access_token: str
    refresh_token: Optional[str]
    scopes: List[str]
    expires_at: Optional[datetime]


def exchange_google_code(
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> TokenResponse:
    """Exchanges Google OAuth code for access and refresh tokens."""
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(token_url, data=payload)
        resp.raise_for_status()
        data = resp.json()

    access_token = data["access_token"]
    refresh_token = data.get("refresh_token")
    expires_in = data.get("expires_in", 3600)
    scope_str = data.get("scope", "")
    scopes = [s.strip() for s in scope_str.split(" ") if s.strip()] if scope_str else ["https://www.googleapis.com/auth/calendar.readonly"]

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        scopes=scopes,
        expires_at=expires_at,
    )


def refresh_google_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> TokenResponse:
    """Refreshes a Google access token using an existing refresh token."""
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(token_url, data=payload)
        resp.raise_for_status()
        data = resp.json()

    access_token = data["access_token"]
    # Google refresh token may not be returned on refresh, reuse existing
    new_refresh = data.get("refresh_token") or refresh_token
    expires_in = data.get("expires_in", 3600)
    scope_str = data.get("scope", "")
    scopes = [s.strip() for s in scope_str.split(" ") if s.strip()] if scope_str else ["https://www.googleapis.com/auth/calendar.readonly"]

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        scopes=scopes,
        expires_at=expires_at,
    )


def exchange_github_code(
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> TokenResponse:
    """Exchanges GitHub OAuth code for access token."""
    token_url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers = {"Accept": "application/json"}
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(token_url, data=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        raise ValueError(f"GitHub OAuth error: {data.get('error_description', data['error'])}")

    access_token = data["access_token"]
    refresh_token = data.get("refresh_token")
    scope_str = data.get("scope", "")
    scopes = [s.strip() for s in scope_str.split(",") if s.strip()] if scope_str else ["repo", "read:user"]

    expires_in = data.get("expires_in")
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in) if expires_in else None

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        scopes=scopes,
        expires_at=expires_at,
    )


def exchange_notion_code(
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> TokenResponse:
    """Exchanges Notion OAuth authorization code for a long-lived access token.

    Key differences from Google/GitHub:
    - Uses HTTP Basic Auth (base64 of client_id:client_secret) in Authorization header.
    - Body must be JSON (not form-encoded).
    - Notion does NOT issue refresh tokens; access tokens are long-lived (no expiry).
    - Returns scopes based on integration capabilities, not a server-returned scope string.
    """
    import base64

    token_url = "https://api.notion.com/v1/oauth/token"
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }
    payload = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(token_url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        raise ValueError(
            f"Notion OAuth error: {data.get('error_description', data.get('error', 'unknown'))}"
        )

    access_token = data["access_token"]
    # Notion does not issue refresh tokens nor explicit expiry — tokens are long-lived.
    return TokenResponse(
        access_token=access_token,
        refresh_token=None,
        scopes=["read_content", "read_user_without_email"],
        expires_at=None,
    )
