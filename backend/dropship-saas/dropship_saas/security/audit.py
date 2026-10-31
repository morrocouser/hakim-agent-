"""
Security audit report and validation utilities for AliDropship SaaS.

- scan_for_secrets: detect hardcoded credentials in strings
- validate_cors_origin: enforce allowed CORS origins strictly
- audit_security_headers: inspect response headers for missing protections
"""
from __future__ import annotations

import os
import re
from typing import Optional

# Basic credential pattern detection (not a replacement for a real secret scanner)
_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|consumer[_-]?key|consumer[_-]?secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
]

_CREDENTIAL_INDICATORS = re.compile(r"(?i)(sk_live_|pk_live_|ghp_|glpat-|xoxb-)")


def scan_for_secrets(text: str) -> list[str]:
    """Return description of any suspicious credential-like strings found."""
    findings: list[str] = []
    for pattern in _SECRET_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(f"Credential pattern: {match.group(0)[:60]}...")
    if _CREDENTIAL_INDICATORS.search(text):
        findings.append("Live credential indicator detected")
    return findings


def validate_cors_origin(origin: Optional[str], allowed_origins: Optional[set[str]] = None) -> bool:
    """Strict CORS origin validation - no wildcards."""
    if not origin:
        return False
    if allowed_origins is None:
        allowed_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
        allowed_origins = {o.strip() for o in allowed_raw.split(",") if o.strip()}
    return origin in allowed_origins


def security_headers_present(response_headers: dict[str, str]) -> dict[str, bool]:
    """Check which security headers are present."""
    lower = {k.lower(): v for k, v in response_headers.items()}
    return {
        "x_content_type_options": "x-content-type-options" in lower,
        "x_frame_options": "x-frame-options" in lower,
        "x_xss_protection": "x-xss-protection" in lower,
        "referrer_policy": "referrer-policy" in lower,
        "strict_transport_security": "strict-transport-security" in lower,
    }