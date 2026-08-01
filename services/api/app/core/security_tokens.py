"""Fernet symmetric encryption at rest for OAuth access and refresh tokens.

Ensures credentials stored in database tables are ciphertexts.
Provides transparent encrypt/decrypt functions for repository consumers.
"""

import base64
from functools import lru_cache
import logging
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_LOCAL_DEV_SALT = b"trellis_local_dev_salt_2026"


@lru_cache(maxsize=1)
def get_fernet_cipher() -> Fernet:
    """Returns Fernet cipher instance based on token_encryption_key setting."""
    settings = get_settings()
    key_str = settings.token_encryption_key

    if key_str and key_str.strip():
        raw_key = key_str.strip()
        try:
            return Fernet(raw_key.encode("utf-8"))
        except Exception:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=_LOCAL_DEV_SALT,
                iterations=100_000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(raw_key.encode("utf-8")))
            return Fernet(key)

    # Local dev / pytest fallback
    logger.warning(
        "TOKEN_ENCRYPTION_KEY missing in config. Using local dev fallback Fernet key. "
        "Do NOT use this fallback in staging/production!"
    )
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_LOCAL_DEV_SALT,
        iterations=100_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(b"trellis_local_default_encryption_secret"))
    return Fernet(key)


def encrypt_token(plain_text: Optional[str]) -> Optional[str]:
    """Encrypts plain_text string returning URL-safe base64 ciphertext."""
    if plain_text is None:
        return None
    cipher = get_fernet_cipher()
    return cipher.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_token(cipher_text: Optional[str]) -> Optional[str]:
    """Decrypts ciphertext string returning original plain_text token."""
    if cipher_text is None:
        return None
    cipher = get_fernet_cipher()
    return cipher.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
