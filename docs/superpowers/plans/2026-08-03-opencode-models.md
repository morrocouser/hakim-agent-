# opencode-models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AXIOM appelle par défaut la passerelle d'inférence Console opencode (modèle gratuit `opencode/deepseek-v4-flash-free`, sans clé) ; OpenRouter reste utilisable via 2 variables d'env.

**Architecture:** 3 variables d'env (`AXIOM_LLM_BASE_URL`, `AXIOM_LLM_API_KEY`, `AXIOM_LLM_MODEL`) deviennent la source de vérité. `LocalAPIClient` (backend/axiom/claude/client.py) résout base + clé + modèle ; `routes.py` expose `llm_provider`/`llm_model` au health et générifie les messages 503. `.env` fige les valeurs par défaut.

**Tech Stack:** Python 3.14, httpx, FastAPI, uvicorn, dotenv. PowerShell 5.1 pour les vérifications.

**Spec:** `docs/superpowers/specs/2026-08-03-opencode-models.md`

## Global Constraints

- PowerShell 5.1 : jamais `&&` ; `-UseBasicParsing` requis sur `Invoke-WebRequest` en session non interactive.
- Pas de repo git → les étapes Commit sont SKIP (noter « no git » dans le rapport).
- Le venv est `C:\Users\hp\Desktop\hakimagent\backend\.venv` (python = `.venv\Scripts\python.exe`).
- Toujours arrêter les processus de test (PIDs des tests uniquement) et vérifier les ports libres.
- Le fichier `backend/.env` contient une vraie clé OpenRouter — ne jamais la supprimer, ne jamais la logger.
- La clé OpenRouter n'est utilisée QUE si la base URL contient `openrouter.ai`.
- Ne modifier QUE : `backend/axiom/claude/client.py`, `backend/axiom/api/routes.py`, `backend/.env`.

---

### Task 1: Résolution base URL + clé API + `is_configured()` dans le client

**Files:**
- Modify: `backend/axiom/claude/client.py:15-19` (constantes) et `:61-76` (`__init__`), `:121-122` (`is_configured`)

**Interfaces:**
- Consumes: rien.
- Produces: `LocalAPIClient.api_key` (str, peut être vide), `LocalAPIClient.base_url` (str), `LocalAPIClient.is_configured() -> bool`.

- [ ] **Step 1: Écrire la vérification qui échoue** — fichier `C:\Users\hp\AppData\Local\Temp\opencode\test_resolution.py` :

```python
import os, subprocess, sys, textwrap

TEST = textwrap.dedent('''
    import os
    from axiom.claude.client import LocalAPIClient, OPENROUTER_API_BASE

    # Scénario 1 : aucune var -> passerelle Console opencode, sans clé
    for k in ("AXIOM_LLM_BASE_URL", "AXIOM_LLM_API_KEY", "OPENCHASSIS_API_BASE", "OPENROUTER_API_KEY"):
        os.environ.pop(k, None)
    c = LocalAPIClient()
    assert c.base_url == "https://console.opencode.ai/inference/openai/v1", c.base_url
    assert c.api_key == "", c.api_key
    assert c.is_configured() is True

    # Scénario 2 : base OpenRouter + clé -> openrouter avec la clé
    os.environ["AXIOM_LLM_BASE_URL"] = OPENROUTER_API_BASE
    os.environ["AXIOM_LLM_API_KEY"] = "sk-or-test"
    c = LocalAPIClient()
    assert c.base_url == OPENROUTER_API_BASE and c.api_key == "sk-or-test"

    # Scénario 3 : base OpenRouter sans AXIOM_LLM_API_KEY -> repli OPENROUTER_API_KEY
    os.environ.pop("AXIOM_LLM_API_KEY", None)
    os.environ["OPENROUTER_API_KEY"] = "sk-or-legacy"
    c = LocalAPIClient()
    assert c.api_key == "sk-or-legacy", c.api_key

    # Scénario 4 : base OpenChassis explicite -> local, is_configured False
    os.environ.pop("OPENROUTER_API_KEY", None)
    os.environ["OPENCHASSIS_API_BASE"] = "http://localhost:20128/v1"
    c = LocalAPIClient()
    assert c.base_url == "http://localhost:20128/v1" and c.is_configured() is False

    print("OK")
''')
r = subprocess.run([sys.executable, "-c", TEST], capture_output=True, text=True)
assert "OK" in r.stdout, r.stdout + r.stderr
print("all scenarios passed")
```

- [ ] **Step 2: Lancer la vérification pour la voir échouer**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe C:\Users\hp\AppData\Local\Temp\opencode\test_resolution.py
```

Expected: FAIL (AssertionError — base_url actuelle = openrouter ou local selon clé).

- [ ] **Step 3: Implémenter dans `client.py`**

Remplacer les constantes (lignes 15-19) :

```python
# API endpoints
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENCODE_CONSOLE_BASE = "https://console.opencode.ai/inference/openai/v1"
LOCAL_API_BASE = os.getenv("OPENCHASSIS_API_BASE", "http://localhost:20128/v1")
APP_REFERRER = "https://github.com/hakimagent/axiom"
APP_TITLE = "AXIOM v4.0 Orchestrateur"
```

Remplacer le corps de `__init__` (lignes 67-75) :

```python
        self.api_key = (api_key or os.getenv("AXIOM_LLM_API_KEY") or "").strip()
        self.base_url = (
            os.getenv("AXIOM_LLM_BASE_URL")
            or LOCAL_API_BASE
            or OPENCODE_CONSOLE_BASE
        )
        if not self.api_key and "openrouter.ai" in self.base_url:
            self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.http = httpx.AsyncClient(timeout=120)
        self.rate_limiter = TokenBucketRateLimiter(rpm=rpm, tpm=tpm)
```

Remplacer `is_configured` (lignes 121-122) :

```python
    def is_configured(self) -> bool:
        return bool(self.api_key) or self.base_url != LOCAL_API_BASE
```

- [ ] **Step 4: Relancer la vérification**

```powershell
.\.venv\Scripts\python.exe C:\Users\hp\AppData\Local\Temp\opencode\test_resolution.py
```

Expected: `all scenarios passed`.

- [ ] **Step 5: Commit — SKIP (pas de repo git).** Écrire le rapport dans `.superpowers/sdd/2026-08-03-opencode-models/task-1-report.md` (statut + sorties verbatim) et retourner au controller.

---

### Task 2: Surcharge du modèle (`AXIOM_LLM_MODEL`) dans `chat()`

**Files:**
- Modify: `backend/axiom/claude/client.py:82-86` (corps de `chat`, body)

**Interfaces:**
- Consumes: `LocalAPIClient.chat(model: str, system: str, messages: list[dict], max_tokens: int = 4096) -> str` (Task 1).
- Produces: comportement — si `AXIOM_LLM_MODEL` défini, le champ `model` de la requête est `AXIOM_LLM_MODEL` quel que soit l'argument `model`.

- [ ] **Step 1: Écrire le test qui échoue** — fichier `C:\Users\hp\AppData\Local\Temp\opencode\test_model_override.py` :

```python
import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from axiom.claude.client import LocalAPIClient

captured = {}

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        captured["body"] = json.loads(self.rfile.read(n))
        captured["auth"] = self.headers.get("Authorization")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "choices": [{"message": {"content": "bonjour"}}]
        }).encode())
    def log_message(self, *a): pass

server = HTTPServer(("127.0.0.1", 18081), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()

os.environ["AXIOM_LLM_BASE_URL"] = "http://127.0.0.1:18081/v1"
for k in ("AXIOM_LLM_API_KEY", "OPENROUTER_API_KEY"):
    os.environ.pop(k, None)
os.environ["AXIOM_LLM_MODEL"] = "opencode/deepseek-v4-flash-free"

c = LocalAPIClient()
import asyncio
out = asyncio.run(c.chat("nvidia/ancien-palier", "sys", [{"role": "user", "content": "hi"}]))
assert out == "bonjour", out
assert captured["body"]["model"] == "opencode/deepseek-v4-flash-free", captured["body"]
assert captured["auth"] is None, "aucun header Authorization attendu (gratuit)"
print("OK")
```

- [ ] **Step 2: Lancer le test pour le voir échouer**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe C:\Users\hp\AppData\Local\Temp\opencode\test_model_override.py
```

Expected: FAIL (AssertionError — model = `nvidia/ancien-palier` envoyé tel quel).

- [ ] **Step 3: Implémenter dans `client.py`** — au début du corps de `chat`, après l'acquisition du rate limiter (ligne 80) :

```python
        model = os.getenv("AXIOM_LLM_MODEL") or model
```

- [ ] **Step 4: Relancer le test**

```powershell
.\.venv\Scripts\python.exe C:\Users\hp\AppData\Local\Temp\opencode\test_model_override.py
```

Expected: `OK`.

- [ ] **Step 5: Commit — SKIP (pas de repo git).** Rapport `task-2-report.md` dans `.superpowers/sdd/2026-08-03-opencode-models/`.

---

### Task 3: Health (`llm_provider`, `llm_model`) + messages 503 génériques

**Files:**
- Modify: `backend/axiom/api/routes.py:48-56` (health), `:40-45` (`require_claude` + message), `:68`, `:78`, `:133` (messages 503)

**Interfaces:**
- Consumes: `LocalAPIClient.base_url` (Task 1).
- Produces: champs health `llm_provider` (str) et `llm_model` (str | None) ; messages 503 sans mention OpenRouter.

- [ ] **Step 1: Écrire la vérification** — fichier `C:\Users\hp\AppData\Local\Temp\opencode\test_health.py` :

```python
import json, os, subprocess, sys, time, urllib.request

os.environ["AXIOM_LLM_BASE_URL"] = "https://console.opencode.ai/inference/openai/v1"
os.environ["AXIOM_LLM_MODEL"] = "opencode/deepseek-v4-flash-free"
for k in ("AXIOM_LLM_API_KEY", "OPENROUTER_API_KEY"):
    os.environ.pop(k, None)

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "axiom.api.main:app", "--host", "127.0.0.1", "--port", "8005"],
    env=os.environ, cwd=os.path.dirname(os.path.abspath(__file__)).replace("\\Temp\\opencode", "\\Desktop\\hakimagent\\backend"),
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
try:
    for _ in range(30):
        try:
            h = json.load(urllib.request.urlopen("http://127.0.0.1:8005/api/v1/health", timeout=2))
            break
        except Exception:
            time.sleep(0.5)
    else:
        raise SystemExit("server never started")
    assert h["agent"] == "AXIOM"
    assert h["llm_provider"] == "opencode-console", h
    assert h["llm_model"] == "opencode/deepseek-v4-flash-free", h
    assert h["openrouter_configured"] is True, h
    print("OK", json.dumps(h, ensure_ascii=False))
finally:
    proc.terminate()
    proc.wait(timeout=5)
```

- [ ] **Step 2: Lancer la vérification pour la voir échouer**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe C:\Users\hp\AppData\Local\Temp\opencode\test_health.py
```

Expected: FAIL (KeyError `llm_provider`).

- [ ] **Step 3: Implémenter dans `routes.py`**

Ajouter une fonction helper après `require_claude` (ligne 45) :

```python
def llm_provider_label() -> str:
    base = claude.base_url if claude else ""
    if "console.opencode.ai" in base:
        return "opencode-console"
    if "openrouter.ai" in base:
        return "openrouter"
    if base == os.getenv("OPENCHASSIS_API_BASE", "http://localhost:20128/v1"):
        return "openchassis"
    return "custom" if base else "none"
```

Remplacer le body du health (lignes 50-55) :

```python
    return {
        "status": "ok",
        "agent": "AXIOM",
        "version": "4.0.0",
        "openrouter_configured": claude.is_configured() if claude else False,
        "llm_provider": llm_provider_label(),
        "llm_model": os.getenv("AXIOM_LLM_MODEL"),
        "memory_tokens": memory.get_total_tokens_estimate(),
    }
```

Remplacer le message de `require_claude` (ligne 44) :

```python
        raise HTTPException(
            status_code=503,
            detail="LLM not configured. Vérifiez AXIOM_LLM_BASE_URL et AXIOM_LLM_API_KEY dans .env"
        )
```

Même message générique pour les trois autres 503 (lignes 68, 78, 133) : remplacer `detail="OpenRouter not configured. Set OPENROUTER_API_KEY in .env"` par `detail="LLM not configured. Vérifiez AXIOM_LLM_BASE_URL et AXIOM_LLM_API_KEY dans .env"`.

- [ ] **Step 4: Relancer la vérification**

```powershell
.\.venv\Scripts\python.exe C:\Users\hp\AppData\Local\Temp\opencode\test_health.py
```

Expected: `OK {"status":"ok","agent":"AXIOM","version":"4.0.0","openrouter_configured":true,"llm_provider":"opencode-console","llm_model":"opencode/deepseek-v4-flash-free",...}`.

- [ ] **Step 5: Commit — SKIP (pas de repo git).** Rapport `task-3-report.md`.

---

### Task 4: `.env` + vérification de bout en bout (chat réel + régression OpenRouter)

**Files:**
- Modify: `backend/.env` (ajout de 3 lignes en fin de fichier)

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: configuration figée de l'app.

- [ ] **Step 1: Ajouter les 3 variables à `backend/.env`** (fin de fichier, au-dessus de toute clé existante) :

```ini
AXIOM_LLM_BASE_URL=https://console.opencode.ai/inference/openai/v1
AXIOM_LLM_MODEL=opencode/deepseek-v4-flash-free
AXIOM_LLM_API_KEY=
```

- [ ] **Step 2: Vérifier que le modèle existe sur la passerelle**

```powershell
$m = Invoke-RestMethod 'https://console.opencode.ai/inference/openai/v1/models' -TimeoutSec 20
($m | ConvertTo-Json -Depth 6) | Select-String -Pattern 'opencode/deepseek-v4-flash-free'
```

Expected: le modèle apparaît dans la liste (sans clé).

- [ ] **Step 3: Chat réel via la passerelle**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
$p = Start-Process -FilePath '.\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','axiom.api.main:app','--host','127.0.0.1','--port','8006' -PassThru
Start-Sleep -Seconds 8
try {
  $body = @{ content = 'Dis bonjour en 5 mots.' } | ConvertTo-Json
  $r = Invoke-RestMethod 'http://127.0.0.1:8006/api/v1/chat' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 120
  Write-Output "response: $($r.response)"
} finally { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
```

Expected: réponse texte du modèle via la passerelle (pas de « [Erreur API] », pas de « [Erreur] »).

- [ ] **Step 4: Régression OpenRouter** (bascule base → openrouter, une requête) :

```powershell
$env:AXIOM_LLM_BASE_URL = 'https://openrouter.ai/api/v1'
$env:AXIOM_LLM_MODEL = $null
$p = Start-Process -FilePath '.\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','axiom.api.main:app','--host','127.0.0.1','--port','8006' -PassThru
Start-Sleep -Seconds 8
try {
  $body = @{ content = 'Dis bonjour en 5 mots.' } | ConvertTo-Json
  $r = Invoke-RestMethod 'http://127.0.0.1:8006/api/v1/chat' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 120
  Write-Output "openrouter_response: $($r.response)"
  $h = Invoke-RestMethod 'http://127.0.0.1:8006/api/v1/health' -TimeoutSec 5
  Write-Output "provider: $($h.llm_provider)"
} finally { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; Remove-Item Env:AXIOM_LLM_BASE_URL -ErrorAction SilentlyContinue }
```

Expected: réponse réelle (clé OpenRouter utilisée) et `provider: openrouter`.

- [ ] **Step 5: Nettoyage + rapport.** Vérifier qu'aucun port 8005/8006 n'écoute plus :

```powershell
Get-NetTCPConnection -LocalPort 8005,8006 -State Listen -ErrorAction SilentlyContinue
```

Rapport `task-4-report.md` (sorties verbatim Steps 2-4 + état des ports). Retourner au controller.
