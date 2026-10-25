"""Tests des correctifs de revue : jetons, IDOR /chat, routes protégées, commandes shell, rate limit."""
from __future__ import annotations

import os
import tempfile
import uuid
from types import SimpleNamespace

import pytest

os.environ.setdefault("HAKIM_JWT_SECRET", "test-secret-for-hardening-tests")
os.environ.setdefault("HAKIM_DB_PATH", os.path.join(tempfile.gettempdir(), "hakim_hardening_test.db"))

from fastapi.testclient import TestClient  # noqa: E402

import axiom.api.main as main_mod  # noqa: E402
from axiom.api.main import app  # noqa: E402
from axiom.api.routes import get_loop  # noqa: E402
from axiom.commands.handlers import CommandHandlers  # noqa: E402
from axiom.commands.registry import CommandRegistry  # noqa: E402
from middleware.rate_limiting import create_rate_limiter  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    # Limiteur neuf par test pour ne pas dépendre de l'ordre d'exécution
    monkeypatch.setattr(main_mod, "rate_limiter", create_rate_limiter(use_redis=False))
    with TestClient(app) as c:  # lance le lifespan => tables créées
        yield c
    app.dependency_overrides.clear()


def _register(client, name=None):
    name = name or f"u_{uuid.uuid4().hex[:10]}"
    r = client.post("/auth/register", json={"username": name, "password": "secret123"})
    assert r.status_code == 200, r.text
    body = r.json()
    client.cookies.clear()
    return name, body["access_token"], body["refresh_token"]


def _bearer(tok):
    return {"Authorization": f"Bearer {tok}"}


# --- 4. jetons ---------------------------------------------------------------

def test_refresh_token_rejected_as_access_token(client):
    _, _, refresh = _register(client)
    assert client.get("/auth/me", headers=_bearer(refresh)).status_code == 401


def test_refresh_rotation_rejects_replay(client):
    _, _, refresh = _register(client)
    first = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert first.status_code == 200
    assert first.json()["refresh_token"] != refresh
    assert client.post("/auth/refresh", json={"refresh_token": refresh}).status_code == 401


def test_access_token_cannot_be_used_to_refresh(client):
    _, access, _ = _register(client)
    assert client.post("/auth/refresh", json={"refresh_token": access}).status_code == 401


def test_logout_revokes_tokens(client):
    _, access, refresh = _register(client)
    assert client.get("/auth/me", headers=_bearer(access)).status_code == 200
    r = client.post("/auth/logout", headers=_bearer(access), cookies={"refresh_token": refresh})
    assert r.status_code == 200
    client.cookies.clear()
    assert client.get("/auth/me", headers=_bearer(access)).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": refresh}).status_code == 401


# --- 3. IDOR /chat -----------------------------------------------------------

def test_chat_cannot_write_into_other_users_conversation(client):
    _, tok_a, _ = _register(client)
    _, tok_b, _ = _register(client)
    convo = client.post("/conversations", json={"title": "privée"}, headers=_bearer(tok_a)).json()

    class FakeLoop:
        async def execute(self, assignment, content):
            res = SimpleNamespace(
                status=SimpleNamespace(value="done"), quality_score=9, iteration=1,
                output="ok", error=None,
            )
            res.model_dump = lambda: {}
            return res

    app.dependency_overrides[get_loop] = lambda: FakeLoop()
    r = client.post("/api/v1/chat", json={"role": "user", "content": "hi", "conversation_id": convo["id"]},
                    headers=_bearer(tok_b))
    assert r.status_code == 404
    # le propriétaire garde l'accès
    r = client.post("/api/v1/chat", json={"role": "user", "content": "hi", "conversation_id": convo["id"]},
                    headers=_bearer(tok_a))
    assert r.status_code == 200
    msgs = client.get(f"/conversations/{convo['id']}", headers=_bearer(tok_a)).json()["messages"]
    assert [m["content"] for m in msgs if m["role"] == "user"] == ["hi"]


# --- 6. routes protégées -----------------------------------------------------

@pytest.mark.parametrize("method,path", [
    ("post", "/api/v1/execute"),
    ("post", "/api/v1/chat/stream"),
    ("get", "/api/v1/memory"),
    ("get", "/api/v1/errors"),
    ("post", "/api/v1/memory/project"),
    ("post", "/api/v1/memory/stack"),
    ("post", "/api/v1/memory/decision"),
    ("post", "/api/v1/errors"),
])
def test_routes_require_authentication(client, method, path):
    kwargs = {} if method == "get" else {"json": {"role": "user", "content": "x", "description": "x"}}
    r = getattr(client, method)(path, **kwargs)
    assert r.status_code == 401


def test_memory_and_error_writes_require_admin(client, monkeypatch):
    monkeypatch.setenv("HAKIM_ADMIN_USERS", "")
    name, tok, _ = _register(client)
    assert client.get("/api/v1/memory", headers=_bearer(tok)).status_code in (200, 503)
    r = client.post("/api/v1/memory/project", params={"name": "x"}, headers=_bearer(tok))
    assert r.status_code == 403
    monkeypatch.setenv("HAKIM_ADMIN_USERS", name)
    r = client.post("/api/v1/memory/project", params={"name": "x"}, headers=_bearer(tok))
    assert r.status_code == 200


# --- 1. commandes shell ------------------------------------------------------

def test_shell_commands_are_admin_only(client, monkeypatch):
    monkeypatch.setenv("HAKIM_ADMIN_USERS", "")
    name, tok, _ = _register(client)
    for cmd in ("/bash", "/git", "/docker", "/npm"):
        r = client.post("/api/v1/commands/execute", params={"command": cmd, "args": "id"}, headers=_bearer(tok))
        assert r.status_code == 403, cmd
    # commande sans sous-processus : autorisée
    r = client.post("/api/v1/commands/execute", params={"command": "/help"}, headers=_bearer(tok))
    assert r.status_code == 200
    # admin : plus de 403 (le binaire peut ensuite être refusé par la liste blanche)
    monkeypatch.setenv("HAKIM_ADMIN_USERS", name)
    r = client.post("/api/v1/commands/execute", params={"command": "/bash", "args": "bash -c id"}, headers=_bearer(tok))
    assert r.status_code == 200
    assert r.json()["success"] is False


@pytest.fixture()
def handlers():
    return CommandHandlers(CommandRegistry())


@pytest.mark.parametrize("cmd", [
    "bash -c id", "sh -c id", "python -c 'print(1)'", "node -e 1",
    "powershell -Command id", "cmd /c dir",
])
def test_interpreters_not_in_allowlist(handlers, cmd):
    res = handlers._run_shell(cmd)
    assert res["success"] is False and "non autorisé" in res["error"]


@pytest.mark.parametrize("args", [
    "-c core.sshCommand=id fetch", "fetch --upload-pack=id origin", "--git-dir=/etc status",
])
def test_git_dangerous_options_rejected(handlers, args):
    assert handlers.handle_git(args)["success"] is False
    assert "non autorisée" in handlers.handle_git(args).get("error", "") or "requise" in handlers.handle_git(args).get("error", "")


def test_commit_message_is_single_argument(handlers, monkeypatch):
    seen = {}
    monkeypatch.setattr("subprocess.run", lambda argv, **kw: seen.update(argv=argv) or SimpleNamespace(returncode=0, stdout="", stderr=""))
    handlers.handle_commit("fix: plusieurs mots -c")
    assert seen["argv"] == ["git", "commit", "-m", "fix: plusieurs mots -c"]


def test_spawns_process_detection(handlers):
    reg = handlers.registry
    assert handlers.spawns_process(reg.get("/bash"))
    assert handlers.spawns_process(reg.get("/commit"))
    assert not handlers.spawns_process(reg.get("/help"))


# --- 2. BashTool / CLI engine -----------------------------------------------

@pytest.mark.asyncio
async def test_cli_engine_bash_denied_without_confirmation(tmp_path):
    from axiom.cli_engine import AxiomCLIEngine
    engine = AxiomCLIEngine(str(tmp_path))
    engine.auto_approve = False
    ok, msg = await engine.execute_tool_call("bash", {"command": "echo hi"})
    assert not ok and "refusée" in msg
    ok, msg = await engine.execute_tool_call("bash", {"command": "echo hi"}, permission_callback=lambda n, a: False)
    assert not ok


@pytest.mark.asyncio
@pytest.mark.parametrize("cmd", ["rm -rf /", "rm  -rf  /", "rm -rf /*", "rm -fr ~", "mkfs.ext4 /dev/sda"])
async def test_bash_tool_denylist_handles_whitespace_variants(tmp_path, cmd):
    from axiom.tools.builtin import BashTool
    res = await BashTool(str(tmp_path)).execute({"command": cmd}, context={})
    assert not res.ok


# --- 5. rate limit auth ------------------------------------------------------

def test_auth_login_is_rate_limited_even_with_rotating_user_agent(client):
    codes = []
    for i in range(12):
        r = client.post("/auth/login", json={"username": "nobody", "password": "x"},
                        headers={"User-Agent": f"ua-{i}"})
        codes.append(r.status_code)
    assert 429 in codes
    assert codes[0] == 401


def test_auth_me_not_under_strict_quota(client):
    _, tok, _ = _register(client)
    assert all(client.get("/auth/me", headers=_bearer(tok)).status_code == 200 for _ in range(10))


# --- 7. sandbox Docker ---------------------------------------------------------

@pytest.mark.parametrize("lang", ["python", "javascript"])
def test_docker_command_is_locked_down(lang):
    from axiom.tools.code_executor import CodeExecutor
    cmd = CodeExecutor(docker_enabled=False)._get_docker_command(lang, "/tmp/x", "")
    joined = " ".join(cmd)
    for flag in ("--read-only", "--cap-drop ALL", "--security-opt no-new-privileges",
                 "--pids-limit", "--network none", "--user 65534:65534", "/tmp/x:/code:ro"):
        assert flag in joined, flag
    assert "--privileged" not in joined


def test_sandbox_script_readable_by_unprivileged_user(tmp_path):
    import stat
    from axiom.tools.code_executor import CodeExecutor
    d = tmp_path / "w"
    d.mkdir(mode=0o700)
    p = CodeExecutor(docker_enabled=False)._write_code_file(str(d), "python", "print(1)")
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o644
    assert stat.S_IMODE(os.stat(d).st_mode) == 0o755


def test_register_then_login_not_blocked_by_shared_quota(client):
    name = f"u_{uuid.uuid4().hex[:10]}"
    for _ in range(3):
        r = client.post("/auth/login", json={"username": name, "password": "x"})
        assert r.status_code == 401  # compteur login seul
    r = client.post("/auth/register", json={"username": name, "password": "secret123"})
    assert r.status_code == 200  # compteur register indépendant
