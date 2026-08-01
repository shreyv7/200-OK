"""CSRF protection for OAuth flow via Fernet-signed state tokens.

Generates and validates state parameters containing user_id, provider, timestamp, and nonce.
Ensures callback request originated from authorized user session and state hasn't expired (30 min TTL).
"""

from datetime import datetime, timezone
import json
import logging
import uuid

from fastapi import HTTPException, status

from app.core.security_tokens import get_fernet_cipher

logger = logging.getLogger(__name__)

STATE_TTL_SECONDS = 1800  # 30 minutes


def generate_oauth_state(user_id: str, provider: str) -> str:
    """Generates an encrypted state string encoding user_id, provider, creation timestamp, and nonce."""
    payload = {
        "user_id": user_id,
        "provider": provider,
        "ts": int(datetime.now(timezone.utc).timestamp()),
        "nonce": str(uuid.uuid4()),
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    cipher = get_fernet_cipher()
    return cipher.encrypt(raw_bytes).decode("utf-8")


def validate_oauth_state(state_token: str, expected_provider: str) -> str:
    """Validates state token and returns user_id if valid.

    Raises HTTPException(403) on decryption failure, provider mismatch, or expiration.
    """
    if not state_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing state parameter in OAuth callback",
        )

    cipher = get_fernet_cipher()
    try:
        decrypted_bytes = cipher.decrypt(state_token.encode("utf-8"))
        payload = json.loads(decrypted_bytes.decode("utf-8"))
    except Exception as e:
        logger.warning(f"OAuth state decryption error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or tampered OAuth state parameter",
        )

    user_id = payload.get("user_id")
    provider = payload.get("provider")
    ts = payload.get("ts", 0)

    if not user_id or provider != expected_provider:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OAuth state provider mismatch",
        )

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if now_ts - ts > STATE_TTL_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OAuth state parameter expired",
        )

    return user_id
