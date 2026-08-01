"""Integration Connection Repository for OAuth connector token management. Owner: Person D.

Handles encrypted token persistence, transparent decryption for authorized connector services,
revocation, and token-free status reporting.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security_tokens import decrypt_token, encrypt_token
from app.models.integration_connection import IntegrationConnection


@dataclass
class DecryptedConnection:
    id: str
    user_id: str
    provider: str
    access_token: str
    refresh_token: Optional[str]
    scopes: List[str]
    connected_at: datetime
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


@dataclass
class ConnectionStatus:
    provider: str
    connected_at: datetime
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    is_active: bool
    scopes: List[str] = field(default_factory=list)


class IntegrationRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_connection(
        self,
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> IntegrationConnection:
        """Upserts an IntegrationConnection record with Fernet-encrypted tokens."""
        encrypted_access = encrypt_token(access_token)
        encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None
        now = datetime.now(timezone.utc)

        stmt = select(IntegrationConnection).where(
            IntegrationConnection.user_id == user_id,
            IntegrationConnection.provider == provider,
        )
        record = self.db.execute(stmt).scalar_one_or_none()

        if record is None:
            record = IntegrationConnection(
                id=str(uuid.uuid4()),
                user_id=user_id,
                provider=provider,
                access_token_encrypted=encrypted_access,
                refresh_token_encrypted=encrypted_refresh,
                scopes=scopes or [],
                connected_at=now,
                revoked_at=None,
                expires_at=expires_at,
            )
            self.db.add(record)
        else:
            record.access_token_encrypted = encrypted_access
            record.refresh_token_encrypted = encrypted_refresh
            record.scopes = scopes or []
            record.connected_at = now
            record.revoked_at = None
            record.expires_at = expires_at

        self.db.commit()
        self.db.refresh(record)
        return record

    def get_active_connection(self, user_id: str, provider: str) -> Optional[DecryptedConnection]:
        """Retrieves and decrypts the active connection tokens for user_id and provider."""
        stmt = select(IntegrationConnection).where(
            IntegrationConnection.user_id == user_id,
            IntegrationConnection.provider == provider,
            IntegrationConnection.revoked_at.is_(None),
        )
        record = self.db.execute(stmt).scalar_one_or_none()

        if record is None:
            return None

        plain_access = decrypt_token(record.access_token_encrypted)
        plain_refresh = decrypt_token(record.refresh_token_encrypted) if record.refresh_token_encrypted else None

        if not plain_access:
            return None

        return DecryptedConnection(
            id=record.id,
            user_id=record.user_id,
            provider=record.provider,
            access_token=plain_access,
            refresh_token=plain_refresh,
            scopes=record.scopes or [],
            connected_at=record.connected_at,
            expires_at=record.expires_at,
            revoked_at=record.revoked_at,
        )

    def revoke_connection(self, user_id: str, provider: str) -> bool:
        """Marks connection as revoked. Ingest jobs must stop immediately."""
        stmt = select(IntegrationConnection).where(
            IntegrationConnection.user_id == user_id,
            IntegrationConnection.provider == provider,
            IntegrationConnection.revoked_at.is_(None),
        )
        record = self.db.execute(stmt).scalar_one_or_none()

        if record is None:
            return False

        record.revoked_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def list_user_connections(self, user_id: str) -> List[ConnectionStatus]:
        """Returns non-sensitive connection status summary for user_id (guaranteed zero tokens)."""
        stmt = select(IntegrationConnection).where(IntegrationConnection.user_id == user_id)
        records = self.db.execute(stmt).scalars().all()

        statuses: List[ConnectionStatus] = []
        for r in records:
            statuses.append(
                ConnectionStatus(
                    provider=r.provider,
                    connected_at=r.connected_at,
                    expires_at=r.expires_at,
                    revoked_at=r.revoked_at,
                    is_active=r.revoked_at is None,
                    scopes=r.scopes or [],
                )
            )

        return statuses
