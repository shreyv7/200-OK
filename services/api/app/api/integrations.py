"""Integrations Router (OAuth Connect, Callback, Status, Revoke). Owner: Person D.

Handles per-provider OAuth redirect URL generation, authorization code exchange,
transparent token refresh, connection revocation, and token-free status reporting.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import List, Literal, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.di import get_current_user_id, get_db
from app.core.oauth_state import generate_oauth_state, validate_oauth_state
from app.integrations.oauth_exchange import (
    exchange_github_code,
    exchange_google_code,
    refresh_google_token,
)
from app.repositories.integration_repository import DecryptedConnection, IntegrationRepository
from app.schemas.integrations import CallbackResponse, ConnectResponse, IntegrationStatusItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])

SUPPORTED_PROVIDERS = {"google-calendar", "github"}


def _validate_provider(provider: str) -> None:
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported provider '{provider}'. Supported providers: {list(SUPPORTED_PROVIDERS)}",
        )


def ensure_fresh_token(
    user_id: str,
    provider: str,
    db: Session,
    settings: Settings,
) -> Optional[DecryptedConnection]:
    """Retrieves active connection for user_id and provider, performing transparent token refresh if expiring.

    If refresh fails, connection is marked revoked and HTTPException(401) is raised with reconnect prompt.
    """
    repo = IntegrationRepository(db)
    conn = repo.get_active_connection(user_id, provider)

    if conn is None or not conn.is_active:
        return None

    # Check if token is nearing expiration (within 5 minutes)
    now = datetime.now(timezone.utc)
    expires_at = conn.expires_at
    if expires_at is not None:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at is not None and expires_at < (now + timedelta(minutes=5)):

        if provider == "google-calendar" and conn.refresh_token:
            client_id = settings.google_oauth_client_id or "stub-client-id"
            client_secret = settings.google_oauth_client_secret or "stub-client-secret"
            try:
                refreshed = refresh_google_token(
                    refresh_token=conn.refresh_token,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                repo.upsert_connection(
                    user_id=user_id,
                    provider=provider,
                    access_token=refreshed.access_token,
                    refresh_token=refreshed.refresh_token,
                    scopes=refreshed.scopes,
                    expires_at=refreshed.expires_at,
                )
                return repo.get_active_connection(user_id, provider)
            except Exception as exc:
                logger.error(f"Transparent token refresh failed for {provider} user {user_id}: {exc}")
                repo.revoke_connection(user_id, provider)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "message": f"Token refresh failed for {provider}. Re-authentication required.",
                        "reconnect_required": True,
                        "provider": provider,
                    },
                )
        elif provider == "google-calendar" and not conn.refresh_token:
            logger.warning(f"Token expired for {provider} and no refresh_token available for user {user_id}")
            repo.revoke_connection(user_id, provider)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": f"Token expired for {provider}. Re-authentication required.",
                    "reconnect_required": True,
                    "provider": provider,
                },
            )

    return conn


@router.get("/status", response_model=List[IntegrationStatusItem])
def get_integrations_status(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> List[IntegrationStatusItem]:
    """Returns non-sensitive integration status summaries for all connected providers for authenticated user."""
    repo = IntegrationRepository(db)
    statuses = repo.list_user_connections(user_id)
    return [
        IntegrationStatusItem(
            provider=s.provider,
            connectedAt=s.connected_at,
            expiresAt=s.expires_at,
            revokedAt=s.revoked_at,
            isActive=s.is_active,
            scopes=s.scopes,
        )
        for s in statuses
    ]


@router.get("/{provider}/connect", response_model=ConnectResponse)
def connect_integration(
    provider: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> ConnectResponse:
    """Generates OAuth authorization redirect URL with CSRF state token."""
    _validate_provider(provider)
    state = generate_oauth_state(user_id, provider)

    if provider == "google-calendar":
        client_id = settings.google_oauth_client_id
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GOOGLE_OAUTH_CLIENT_ID is not configured in .env",
            )
        redirect_uri = settings.google_oauth_redirect_uri
        scope = "https://www.googleapis.com/auth/calendar.readonly"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    elif provider == "github":
        client_id = settings.github_oauth_client_id
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GITHUB_OAUTH_CLIENT_ID is not configured in .env",
            )
        redirect_uri = settings.github_oauth_redirect_uri
        scope = "repo,read:user"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
        }
        auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported provider")

    return ConnectResponse(auth_url=auth_url)


@router.get("/{provider}/callback", response_model=CallbackResponse)
def oauth_callback(
    provider: str,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str = Query(..., description="CSRF state parameter"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CallbackResponse:
    """Handles OAuth callback, validates state token, exchanges code for credentials, and persists encrypted tokens."""
    _validate_provider(provider)
    user_id = validate_oauth_state(state, expected_provider=provider)

    repo = IntegrationRepository(db)

    if provider == "google-calendar":
        client_id = settings.google_oauth_client_id
        client_secret = settings.google_oauth_client_secret
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET not configured in .env",
            )
        redirect_uri = settings.google_oauth_redirect_uri
        tokens = exchange_google_code(
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            client_secret=client_secret,
        )
    elif provider == "github":
        client_id = settings.github_oauth_client_id
        client_secret = settings.github_oauth_client_secret
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GITHUB_OAUTH_CLIENT_ID or GITHUB_OAUTH_CLIENT_SECRET not configured in .env",
            )
        redirect_uri = settings.github_oauth_redirect_uri
        tokens = exchange_github_code(
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            client_secret=client_secret,
        )
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported provider")


    repo.upsert_connection(
        user_id=user_id,
        provider=provider,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        scopes=tokens.scopes,
        expires_at=tokens.expires_at,
    )

    return CallbackResponse(
        provider=provider,
        connected=True,
        scopes=tokens.scopes,
    )


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_integration(
    provider: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> Response:
    """Revokes OAuth integration connection for user_id and provider. Ingest jobs stop immediately."""
    _validate_provider(provider)
    repo = IntegrationRepository(db)
    success = repo.revoke_connection(user_id, provider)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active connection found for provider '{provider}'",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
