"""AES-256-GCM encryption for API tokens and credentials."""

from __future__ import annotations
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


def _get_key() -> bytes:
    """Get encryption key from env or default (dev only)."""
    key_hex = os.environ.get("ENCRYPTION_KEY", "0" * 64)
    return bytes.fromhex(key_hex)


def encrypt(plaintext: str, key: bytes | None = None) -> str:
    """Encrypt a string with AES-256-GCM. Returns base64-encoded iv:authTag:ciphertext."""
    if key is None:
        key = _get_key()
    
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    
    # iv(12 bytes):authTag(16 bytes):ciphertext(rest)
    iv_hex = nonce.hex()
    # AESGCM appends authTag to ciphertext, so we split it
    tag = ciphertext[-16:]
    data = ciphertext[:-16]
    
    combined = bytes.fromhex(iv_hex) + tag + data
    return base64.b64encode(combined).decode("utf-8")


def decrypt(ciphertext_b64: str, key: bytes | None = None) -> str:
    """Decrypt AES-256-GCM encrypted string."""
    if key is None:
        key = _get_key()
    
    combined = base64.b64decode(ciphertext_b64)
    iv = combined[:12]
    tag = combined[12:28]
    data = combined[28:]
    
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, data + tag, None)
    return plaintext.decode("utf-8")


def encrypt_token(access_token: str) -> str:
    """Encrypt a Shopify/WooCommerce access token."""
    return encrypt(access_token)


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a Shopify/WooCommerce access token."""
    return decrypt(encrypted_token)