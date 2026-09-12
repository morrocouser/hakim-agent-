"""Smoke tests for the P0 security wiring.

Verifies:
- Auth-gated routes (/chat, /tools/*, /commands/execute) reject requests
  without an Authorization header.
- A valid token that decodes but references a missing user_id returns
  a 401 from the auth dependency (proves the token was decoded and the
  DB lookup ran — the gate is on).
- Public routes (/health, /skills) respond without auth.
- Rate-limit headers are attached to allowed responses.
- The server refuses to start if HAKIM_JWT_SECRET is missing.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Skip this whole module if the JWT secret isn't set; the env is required
# for the app to even import (the auth module raises at import time).
if not os.getenv("HAKIM_JWT_SECRET"):
    pytest.skip(
        "HAKIM_JWT_SECRET not set — skipping smoke tests (set it to run).",
        allow_module_level=True,
    )

from fastapi.testclient import TestClient  # noqa: E402

from axiom.api.main import app  # noqa: E402
from axiom.auth.jwt import create_access_token  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_chat_requires_auth(client: TestClient) -> None:
    r = client.post("/api/v1/chat", json={"role": "user", "content": "hi"})
    assert r.status_code == 401


def test_tools_code_requires_auth(client: TestClient) -> None:
    r = client.post("/api/v1/tools/code", params={"language": "python", "code": "print(1)"})
    assert r.status_code == 401


def test_tools_file_requires_auth(client: TestClient) -> None:
    r = client.post("/api/v1/tools/file", params={"path": "test.txt", "content": "x"})
    assert r.status_code == 401


def test_tools_search_requires_auth(client: TestClient) -> None:
    r = client.post("/api/v1/tools/search", params={"query": "x"})
    assert r.status_code == 401


def test_commands_execute_requires_auth(client: TestClient) -> None:
    r = client.post("/api/v1/commands/execute", params={"command": "help"})
    assert r.status_code == 401


def test_health_is_public(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code in (200, 503)


def test_skills_is_public(client: TestClient) -> None:
    r = client.get("/api/v1/skills")
    assert r.status_code == 200


def test_rate_limit_header_on_allowed_response(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    # Lowercased check; Starlette/FastAPI normalizes
    assert "x-ratelimit-remaining" in {k.lower() for k in r.headers.keys()}


def test_valid_token_reaches_db_lookup(client: TestClient) -> None:
    """A real-shaped token (no user in DB) should pass the header check and
    reach the user-lookup step, which fails because the user_id doesn't exist.
    This proves the auth dependency is on, not bypassed."""
    token = create_access_token({"user_id": 99999, "username": "ghost"})
    r = client.post(
        "/api/v1/chat",
        json={"role": "user", "content": "hi"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 401
    assert "Utilisateur non trouvé" in r.text or "Token invalide" in r.text


def test_server_refuses_to_start_without_secret() -> None:
    """The auth module (jwt.py) must raise RuntimeError if HAKIM_JWT_SECRET
    is absent from the environment. We test this by importing jwt.py directly
    in a subprocess whose environment has the variable removed.

    We must also prevent routes.py's load_dotenv() from re-populating the
    variable from .env, so we point DOTENV_PATH to /dev/null via a
    sitecustomize that clears the env before import."""
    backend_dir = Path(__file__).resolve().parent.parent
    # Build env without HAKIM_JWT_SECRET
    env = {k: v for k, v in os.environ.items() if k != "HAKIM_JWT_SECRET"}
    # Also prevent load_dotenv from finding the .env file
    env["HAKIM_JWT_SECRET"] = ""

    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import axiom.auth.jwt",
        ],
        cwd=str(backend_dir),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode != 0, (
        f"subprocess should have failed without HAKIM_JWT_SECRET.\n"
        f"rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )
    assert "HAKIM_JWT_SECRET" in proc.stderr or "HAKIM_JWT_SECRET" in proc.stdout