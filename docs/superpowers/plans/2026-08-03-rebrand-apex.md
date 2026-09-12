# rebrand-apex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Renommer la marque visible AXIOM → APEX et intégrer les logos (`apex-icon-192.png`, `apex-icon-favicon.png`) — fenêtre Qt « APEX » avec icône, frontend « APEX » avec logo, health `agent: "APEX"`.

**Architecture:** Renommage de marque uniquement — le package Python `axiom`, les scripts (`axiom-desktop`...), le nom de package `axiom-4.0.0` et la clé localStorage `axiom_state_v1` restent. 4 tasks : backend core → fenêtre Qt → frontend → vérification e2e. **À exécuter APRÈS le plan opencode-models** (mêmes fichiers `routes.py`/`client.py`).

**Tech Stack:** Python 3.14, PySide6, Next 16 (export statique), PowerShell 5.1.

**Spec:** `docs/superpowers/specs/2026-08-03-rebrand-apex.md`

## Global Constraints

- PowerShell 5.1 : jamais `&&` ; `-UseBasicParsing` requis sur `Invoke-WebRequest` en session non interactive.
- Pas de repo git → les étapes Commit sont SKIP (noter « no git » dans le rapport).
- Le venv est `C:\Users\hp\Desktop\hakimagent\backend\.venv`.
- Toujours arrêter les processus de test (PIDs des tests uniquement) ; vérifier les ports libres après.
- **Interdits de toucher** : modules Python `axiom/` internes (chemins/imports), scripts (pyproject), clé localStorage `axiom_state_v1` (`frontend/lib/storage.ts`), `.env`, docs.
- Logos sources : `C:\Users\hp\Desktop\hakimagent\apex-icon-192.png`, `apex-icon-512.png`, `apex-icon-favicon.png`, `apex-icon.svg` (rester à la racine ; on en fait des COPIES).
- Ne modifier QUE les fichiers listés dans les tasks (le frontend : uniquement textes visibles + metadata + 2 copies de logo).

---

### Task 1: Backend core — health `agent: "APEX"`, APP_TITLE, prompt système, TUI, ancienne app desktop

**Files:**
- Modify: `backend/axiom/api/routes.py:52` (`"agent": "AXIOM"` → `"agent": "APEX"`)
- Modify: `backend/axiom/claude/client.py:18` (`APP_TITLE`)
- Modify: `backend/axiom/core/system_prompt.py:14` (1ère ligne du prompt)
- Modify: `backend/cli/tui/app.py`, `backend/cli/tui/screens/help_screen.py`, `backend/desktop/main_window.py`, `backend/desktop/main.py` (titres/mentions visibles « AXIOM » → « APEX »)

**Interfaces:**
- Consumes: rien (après le plan opencode-models : `routes.py` a déjà `llm_provider`, messages 503 génériques).
- Produces: `GET /api/v1/health` → `"agent": "APEX"` ; `APP_TITLE = "APEX v4.0 Orchestrateur"` ; prompt système commençant par « Tu es APEX, un agent IA orchestrateur... ».

- [ ] **Step 1: Écrire la vérification qui échoue** — fichier `C:\Users\hp\AppData\Local\Temp\opencode\test_rebrand_core.py` :

```python
import json, os, subprocess, sys, time, urllib.request, re

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "axiom.api.main:app", "--host", "127.0.0.1", "--port", "8007"],
    cwd=r"C:\Users\hp\Desktop\hakimagent\backend", env=os.environ,
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
try:
    for _ in range(30):
        try:
            h = json.load(urllib.request.urlopen("http://127.0.0.1:8007/api/v1/health", timeout=2))
            break
        except Exception:
            time.sleep(0.5)
    else:
        raise SystemExit("server never started")
    assert h["agent"] == "APEX", h

    with open(r"C:\Users\hp\Desktop\hakimagent\backend\axiom\core\system_prompt.py", encoding="utf-8") as f:
        prompt = f.read()
    assert "Tu es APEX," in prompt and "Tu es AXIOM," not in prompt

    with open(r"C:\Users\hp\Desktop\hakimagent\backend\axiom\claude\client.py", encoding="utf-8") as f:
        client_src = f.read()
    assert 'APP_TITLE = "APEX v4.0 Orchestrateur"' in client_src
    print("OK", h)
finally:
    proc.terminate(); proc.wait(timeout=5)
```

- [ ] **Step 2: Lancer pour voir échouer**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe C:\Users\hp\AppData\Local\Temp\opencode\test_rebrand_core.py
```

Expected: FAIL (AssertionError `agent == "APEX"`).

- [ ] **Step 3: Implémenter**

`backend/axiom/api/routes.py:52` :
```python
        "agent": "APEX",
```

`backend/axiom/claude/client.py:18` :
```python
APP_TITLE = "APEX v4.0 Orchestrateur"
```

`backend/axiom/core/system_prompt.py:14` — uniquement la première phrase :
```python
AXIOM_SYSTEM_PROMPT = """Tu es APEX, un agent IA orchestrateur de classe entreprise. ...
```

`backend/cli/tui/app.py`, `backend/cli/tui/screens/help_screen.py`, `backend/desktop/main_window.py`, `backend/desktop/main.py` : remplacer les chaînes VISIBLES « AXIOM » par « APEX » (titres de fenêtres, headers TUI, à propos) — utiliser un remplacement global `AXIOM` → `APEX` limité aux littéraux d'affichage ; NE PAS renommer identifiants/classes/fonctions (ex. `app.setWindowTitle("AXIOM ...")` → `"APEX ..."`, mais pas `class AxiomWindow`).

- [ ] **Step 4: Relancer la vérification**

```powershell
.\.venv\Scripts\python.exe C:\Users\hp\AppData\Local\Temp\opencode\test_rebrand_core.py
```

Expected: `OK {"status":"ok","agent":"APEX",...}`.

- [ ] **Step 5: Vérification compile + rapide**

```powershell
.\.venv\Scripts\python.exe -m py_compile axiom\api\routes.py axiom\claude\client.py axiom\core\system_prompt.py cli\tui\app.py cli\tui\screens\help_screen.py desktop\main_window.py desktop\main.py; if ($?) { Write-Output "py_compile: OK" }
```

- [ ] **Step 6: Commit — SKIP (pas de repo git).** Rapport `task-1-report.md` dans `.superpowers/sdd/2026-08-03-rebrand-apex/`.

---

### Task 2: Fenêtre Qt — titre « APEX », icône, `detect_axiom` renommé

**Files:**
- Modify: `backend/desktop/web_app.py:35` (`detect_axiom`), `:110` (`setWindowTitle`), `:164` (titre chargement), `:194` (`setApplicationName`)
- Create: `backend/desktop/resources/apex-icon.png` (copie de `apex-icon-192.png`)

**Interfaces:**
- Consumes: `detect_axiom` (Task 1 du plan app-native, ligne 31-37) — la valeur comparée devient `"APEX"`.
- Produces: fenêtre titre « APEX », icône fenêtre + taskbar, `app.setApplicationName("APEX")`.

- [ ] **Step 1: Copier le logo dans les resources**

```powershell
Copy-Item 'C:\Users\hp\Desktop\hakimagent\apex-icon-192.png' 'C:\Users\hp\Desktop\hakimagent\backend\desktop\resources\apex-icon.png'
Test-Path 'C:\Users\hp\Desktop\hakimagent\backend\desktop\resources\apex-icon.png'
```

Expected: `True`.

- [ ] **Step 2: Implémenter dans `web_app.py`**

Imports (après ligne 4, section PySide6 existante lignes 100-104) — ajouter QIcon :
```python
from PySide6.QtGui import QIcon
```

`detect_axiom` ligne 35 :
```python
        return r.json().get("agent") == "APEX"
```

`WebAppWindow.__init__` ligne 110 :
```python
        self.setWindowTitle("APEX")
```

Après `self.resize(1280, 800)` (ligne 111), ajouter l'icône :
```python
        icon_path = Path(__file__).parent / "resources" / "apex-icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
```

`_on_progress` ligne 164 :
```python
            self.setWindowTitle(f"APEX — chargement {progress}%")
```

`_on_loaded` ligne 167 :
```python
        self.setWindowTitle("APEX")
```

`main()` ligne 194 :
```python
    app.setApplicationName("APEX")
```

Ligne 196 : `app.setOrganizationName("APEX")` — ⚠️ le changement de (org, app) déplace le profil QtWebEngine (localStorage du webview) vers un dossier neuf : l'état stocké des sessions précédentes est réinitialisé (acceptable en pré-release ; la clé `axiom_state_v1` reste dans le code). Le noter dans le rapport.

Après `app.setOrganizationName("APEX")` (ligne 196), ajouter l'icône app :
```python
    icon_path = Path(__file__).parent / "resources" / "apex-icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
```

- [ ] **Step 3: Vérifier le titre de la fenêtre + santé backend**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe -c "import os, sys; from PySide6.QtWidgets import QApplication; from desktop.web_app import WebAppWindow; app = QApplication(sys.argv); w = WebAppWindow(); print('title:', w.windowTitle()); sys.exit(0)"
```

Expected: `title: APEX` (le constructeur peut démarrer le serveur embarqué en thread daemon — le process se termine, le thread meurt avec lui ; si port 8000 occupé par un test précédent, arrêter d'abord).

- [ ] **Step 4: Lancement réel + health**

```powershell
$p = Start-Process -FilePath '.\.venv\Scripts\axiom-desktop.exe' -PassThru
Start-Sleep -Seconds 12
Write-Output "alive: $(-not $p.HasExited)"
$h = Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 5
Write-Output "health: $($h | ConvertTo-Json -Compress)"
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
```

Expected: `alive: True` et `health: {... "agent":"APEX" ...}` (la fenêtre s'affiche avec icône + titre « APEX » — attesté par le lancement réel).

- [ ] **Step 5: Commit — SKIP (pas de repo git).** Rapport `task-2-report.md`.

---

### Task 3: Frontend — metadata « APEX », favicon, logo sidebar, textes visibles, rebuild

**Files:**
- Modify: `frontend/app/layout.tsx:6` (title metadata)
- Create: `frontend/app/icon.png` (copie `apex-icon-favicon.png`)
- Create: `frontend/public/apex-icon-192.png` (copie)
- Modify: `frontend/components/Sidebar.tsx:33-46` (bloc logo)
- Modify: `frontend/components/ChatPanel.tsx:34,58,129` (textes)
- Modify: `frontend/app/page.tsx:65,343,345,347,456,480,515,648` (textes)
- Modify: `frontend/app/chat/page.tsx:69,117` (textes)

**Interfaces:**
- Consumes: rien (frontend 100 % client).
- Produces: build statique `frontend/out/` avec title « APEX », `icon.png` (favicon), sidebar logo + « APEX ».

- [ ] **Step 1: Copier les logos**

```powershell
Copy-Item 'C:\Users\hp\Desktop\hakimagent\apex-icon-favicon.png' 'C:\Users\hp\Desktop\hakimagent\frontend\app\icon.png'
New-Item -ItemType Directory -Path 'C:\Users\hp\Desktop\hakimagent\frontend\public' -Force | Out-Null
Copy-Item 'C:\Users\hp\Desktop\hakimagent\apex-icon-192.png' 'C:\Users\hp\Desktop\hakimagent\frontend\public\apex-icon-192.png'
```

- [ ] **Step 2: `layout.tsx` ligne 6**

```tsx
  title: 'HakimAgent / APEX v4.0 — Orchestrateur Multi-Agents IA',
```

- [ ] **Step 3: `Sidebar.tsx` — bloc logo (lignes 33-46) : image + « APEX » à la place du monogramme « A »**

```tsx
      <div className="flex items-center gap-3 px-5 pt-5 pb-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/apex-icon-192.png"
          alt="Logo APEX"
          width={38}
          height={38}
          className="shrink-0"
          style={{ borderRadius: 8 }}
        />
        <div>
          <div
            className="font-bold text-sm tracking-wide"
            style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}
          >
            HakimAgent
          </div>
          <div className="text-mono" style={{ color: 'var(--accent)', fontSize: 10 }}>
            APEX v4.0
          </div>
        </div>
      </div>
```

- [ ] **Step 4: Textes visibles restants** — remplacements simples « AXIOM » → « APEX » dans les littéraux d'affichage uniquement. **Exclusions formelles** : identifiants/classes (ex. `input-axiom`, `bg-axiom-card`, `text-axiom-*`, `AxiomState`), clé localStorage `axiom_state_v1`, imports. Procédure : lancer `Select-String -Path 'components\ChatPanel.tsx','app\chat\page.tsx','app\page.tsx' -Pattern 'AXIOM'` et traiter chaque occurrence non exclue jusqu'à n'en laisser aucune. Emplacements connus :
  - `components/ChatPanel.tsx:34` (message erreur API), `:58` (« APEX Prêt »), `:129` (aria-label)
  - `app/page.tsx:65` (`name: 'APEX'`), `:343` (`|| 'APEX'`), `:345`, `:347` (messages erreur backend), `:456` (« APEX v4 »), `:480` (« APEX »), `:515` (« APEX sélectionne... »), `:648` (placeholder)
  - `app/chat/page.tsx:66-70` (empty state « APEX Prêt »), `:117` (`'APEX'`)

- [ ] **Step 5: Rebuild + typecheck**

```powershell
cd C:\Users\hp\Desktop\hakimagent\frontend
npm run build 2>&1 | Select-Object -Last 3
npx tsc --noEmit
```

Expected: build OK (7 pages statiques), `tsc` code 0.

- [ ] **Step 6: Vérifier le build**

```powershell
Test-Path 'C:\Users\hp\Desktop\hakimagent\frontend\out\icon.png'
Select-String -Path 'C:\Users\hp\Desktop\hakimagent\frontend\out\index.html' -Pattern 'APEX' | Select-Object -First 1
```

Expected: `True` (icon.png dans le build) + une occurrence d'« APEX » dans le HTML.

- [ ] **Step 7: Commit — SKIP (pas de repo git).** Rapport `task-3-report.md`.

---

### Task 4: Vérification de bout en bout — app native « APEX » avec logo

**Files:** aucun (vérifications uniquement).

**Interfaces:**
- Consumes: Tasks 1-3.

- [ ] **Step 1: Lancer l'app native et vérifier health + page servie**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
$p = Start-Process -FilePath '.\.venv\Scripts\axiom-desktop.exe' -PassThru
Start-Sleep -Seconds 15
Write-Output "alive: $(-not $p.HasExited)"
$h = Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 5
Write-Output "health: $($h | ConvertTo-Json -Compress)"
$w = Invoke-WebRequest 'http://127.0.0.1:8000/' -TimeoutSec 5 -UseBasicParsing
Write-Output "root: $($w.StatusCode) $($w.Headers['Content-Type'])"
$ico = Invoke-WebRequest 'http://127.0.0.1:8000/icon.png' -TimeoutSec 5 -UseBasicParsing
Write-Output "icon: $($ico.StatusCode) $($ico.Headers['Content-Type'])"
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
```

Expected: `alive: True`, health avec `"agent":"APEX"`, `root: 200 text/html; charset=utf-8`, `icon: 200 image/png`.

- [ ] **Step 2: Double instance (détection « APEX »)** — la 2ᵉ instance doit réutiliser le serveur existant (le health renommé est détecté) :

```powershell
$p1 = Start-Process -FilePath '.\.venv\Scripts\axiom-desktop.exe' -PassThru
Start-Sleep -Seconds 12
$p2 = Start-Process -FilePath '.\.venv\Scripts\axiom-desktop.exe' -PassThru
Start-Sleep -Seconds 10
Write-Output "p1: $(-not $p1.HasExited)  p2: $(-not $p2.HasExited)"
$h = Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 5
Write-Output "health: $($h | ConvertTo-Json -Compress)"
Stop-Process -Id $p1.Id,$p2.Id -Force -ErrorAction SilentlyContinue
```

Expected: `p1: True  p2: True` et health `agent: APEX` (pas de message « Un serveur AXIOM sans interface web... »).

- [ ] **Step 3: Nettoyage + rapport.** Vérifier qu'aucun port 8000/8007 n'écoute plus :

```powershell
Get-NetTCPConnection -LocalPort 8000,8007 -State Listen -ErrorAction SilentlyContinue
```

Rapport `task-4-report.md` (sorties verbatim + état des ports + constat visuel fenêtre « APEX » avec logo, tel qu'observé pendant les lancements réels). Retourner au controller.
