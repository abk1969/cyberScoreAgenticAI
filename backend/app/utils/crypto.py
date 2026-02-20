"""Encryption utilities for CyberScore.

Provides AES-256-GCM encryption for data at rest and
helper functions for secure token generation.
All keys must come from environment variables or HSM — NEVER hardcoded.
"""

import base64
import hashlib
import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_encryption_key() -> bytes:
    """Generate a random 256-bit AES key.

    Returns:
        32-byte random key for AES-256.
    """
    return AESGCM.generate_key(bit_length=256)


def encrypt_data(plaintext: str, key: bytes) -> str:
    """Encrypt plaintext using AES-256-GCM.

    Args:
        plaintext: The string to encrypt.
        key: 32-byte AES-256 key.

    Returns:
        Base64-encoded string of nonce + ciphertext + tag.
    """
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_data(encrypted: str, key: bytes) -> str:
    """Decrypt AES-256-GCM encrypted data.

    Args:
        encrypted: Base64-encoded nonce + ciphertext + tag.
        key: 32-byte AES-256 key.

    Returns:
        Decrypted plaintext string.

    Raises:
        cryptography.exceptions.InvalidTag: If decryption fails.
    """
    raw = base64.b64decode(encrypted)
    nonce = raw[:12]
    ciphertext = raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token.

    Args:
        length: Number of random bytes (default 32 = 256 bits).

    Returns:
        URL-safe base64-encoded token string.
    """
    return secrets.token_urlsafe(length)


def hash_value(value: str, salt: str | None = None) -> str:
    """Create a SHA-256 hash of a value with optional salt.

    Args:
        value: The string to hash.
        salt: Optional salt prepended to value.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    data = f"{salt or ''}{value}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()
