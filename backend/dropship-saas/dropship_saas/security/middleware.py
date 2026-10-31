"""
Security middleware for AliDropship SaaS Platform.

- Rate limiting via slowapi (wraps FastAPI app)
- Security headers: X-Content-Type-Options, X-Frame-Options,
  X-XSS-Protection, Strict-Transport-Security (configurable for dev)
- Input sanitization helpers for URL/user-supplied strings
"""
from __future__ import annotations

import re
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

log = logging.getLogger("dropship_saas.security.middleware")

# Block common SSRF/internal URL patterns
_SSRF_PATTERNS = re.compile(
    r"^(https?://)?("
    r"127\.0\.0\.1|localhost|0\.0\.0\.0|169\.254\.169\.254|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}"
    r")(?::\d+)?/.*$",
    re.IGNORECASE,
)

_ALLOWED_URL_SCHEMES = frozenset({"http", "https"})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if request.url.scheme == "https" or os.environ.get("FORCE_HSTS") == "1":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


def sanitize_url(url: str) -> str:
    """Strip dangerous characters from a user-supplied URL string."""
    return url.replace("\n", "").replace("\r", "").strip()


def is_safe_url(url: str, *, allowed_hosts: Optional[set[str]] = None) -> bool:
    """Reject SSRF / internal-network / non-http URLs."""
    cleaned = sanitize_url(url).lower()
    if _SSRF_PATTERNS.match(cleaned):
        return False
    if "://" in cleaned:
        scheme = cleaned.split("://", 1)[0]
        if scheme not in _ALLOWED_URL_SCHEMES:
            return False
    if allowed_hosts:
        from urllib.parse import urlparse
        host = urlparse(cleaned).hostname
        if host and host not in allowed_hosts:
            return False
    return True


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    return PlainTextResponse("Rate limit exceeded", status_code=429)