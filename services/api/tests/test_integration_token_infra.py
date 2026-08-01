"""Unit and repository tests for Person D Task D1 (Token Storage & At-Rest Encryption Infra).

Validates Fernet encryption/decryption roundtrips, database column ciphertext verification,
repository upsert/active retrieval/revocation, and non-leakage of tokens in status models.
Runs natively via pytest.
"""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.security_tokens import decrypt_token, encrypt_token
from app.models.base import Base
from app.models.integration_connection import IntegrationConnection
from app.repositories.integration_repository import IntegrationRepository


@pytest.fixture
def db_session():
    """In-memory SQLite database session fixture."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_fernet_encryption_roundtrip():
    """Test 1: Encrypt string -> decrypt string returns exact original token."""
    secret_token = "gho_16678234abcdef9081234567890abcdef"
    cipher_text = encrypt_token(secret_token)

    assert cipher_text is not None
    assert cipher_text != secret_token
    assert "gho_" not in cipher_text

    decrypted = decrypt_token(cipher_text)
    assert decrypted == secret_token


def test_ciphertext_in_database_column(db_session):
    """Test 2: Direct query on DB column asserts access_token_encrypted is ciphertext, not plaintext."""
    repo = IntegrationRepository(db_session)
    plain_token = "ya29.a0Axoo-secret_google_oauth_access_token_12345"

    repo.upsert_connection(
        user_id="user_test_d1",
        provider="google_calendar",
        access_token=plain_token,
        refresh_token="1//04_refresh_secret",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    )

    # Directly inspect raw SQLAlchemy row
    stmt = select(IntegrationConnection).where(
        IntegrationConnection.user_id == "user_test_d1",
        IntegrationConnection.provider == "google_calendar",
    )
    raw_record = db_session.execute(stmt).scalar_one()

    # DB column MUST NOT contain plaintext token substring
    assert raw_record.access_token_encrypted != plain_token
    assert "ya29.a0Axoo" not in raw_record.access_token_encrypted
    assert "google_oauth" not in raw_record.access_token_encrypted

    assert raw_record.refresh_token_encrypted != "1//04_refresh_secret"
    assert "refresh_secret" not in raw_record.refresh_token_encrypted


def test_repository_upsert_and_decryption(db_session):
    """Test 3: Upsert connection -> get_active_connection decrypts to original tokens."""
    repo = IntegrationRepository(db_session)
    access = "gho_sample_github_token_999"
    refresh = "ghr_sample_refresh_token_888"
    expires = datetime.now(timezone.utc) + timedelta(hours=1)

    repo.upsert_connection(
        user_id="user_test_d1",
        provider="github",
        access_token=access,
        refresh_token=refresh,
        scopes=["repo", "read:user"],
        expires_at=expires,
    )

    active = repo.get_active_connection("user_test_d1", "github")
    assert active is not None
    assert active.user_id == "user_test_d1"
    assert active.provider == "github"
    assert active.access_token == access
    assert active.refresh_token == refresh
    assert active.scopes == ["repo", "read:user"]
    assert active.is_active is True


def test_connection_revocation(db_session):
    """Test 4: Revoking connection sets revoked_at and get_active_connection returns None."""
    repo = IntegrationRepository(db_session)
    repo.upsert_connection(
        user_id="user_test_d1",
        provider="google_calendar",
        access_token="token_to_revoke",
    )

    # Active before revoke
    assert repo.get_active_connection("user_test_d1", "google_calendar") is not None

    # Revoke
    revoked = repo.revoke_connection("user_test_d1", "google_calendar")
    assert revoked is True

    # Inactive after revoke
    assert repo.get_active_connection("user_test_d1", "google_calendar") is None

    # List connections shows inactive
    statuses = repo.list_user_connections("user_test_d1")
    assert len(statuses) == 1
    assert statuses[0].provider == "google_calendar"
    assert statuses[0].is_active is False
    assert statuses[0].revoked_at is not None


def test_connection_status_summary_omits_tokens(db_session):
    """Test 5: ConnectionStatus objects contain no token fields whatsoever."""
    repo = IntegrationRepository(db_session)
    repo.upsert_connection(
        user_id="user_test_d1",
        provider="github",
        access_token="super_secret_access_token",
        refresh_token="super_secret_refresh_token",
    )

    statuses = repo.list_user_connections("user_test_d1")
    assert len(statuses) == 1
    status = statuses[0]

    # ConnectionStatus fields
    assert not hasattr(status, "access_token")
    assert not hasattr(status, "refresh_token")
    assert not hasattr(status, "access_token_encrypted")
    assert not hasattr(status, "refresh_token_encrypted")
    assert status.provider == "github"
    assert status.is_active is True
