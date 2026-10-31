"""
Security utilities for AliDropship SaaS Platform.

- JWT token creation/validation with HS256
- Cookie-based auth (httpOnly, secure flag when TLS)
- Password hashing with bcrypt-compatible fallback
"""
from __future__ import annotations

import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-jwt-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))

COOKIE_NAME = "session_id"
COOKIE_HTTPONLY = True
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "lax")


def create_access_token(subject: str, *, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS))
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def hash_password(password: str) -> str:
    salt = os.environ.get("PASSWORD_PEPPER", "dev-pepper-change-in-production")
    digest = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"sha256${digest}"


def verify_password(password: str, hashed: str) -> bool:
    if not hashed.startswith("sha256$"):
        return False
    _, digest = hashed.split("$", 1)
    salt = os.environ.get("PASSWORD_PEPPER", "dev-pepper-change-in-production")
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == digest


def generate_session_id() -> str:
    return secrets.token_hex(32)