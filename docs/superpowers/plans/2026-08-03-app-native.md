# App Native AXIOM (Fenêtre Qt + Backend embarqué) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Une seule commande `axiom-desktop` lance une fenêtre native PySide6 affichant le frontend web AXIOM avec le backend FastAPI embarqué dans un thread invisible.

**Architecture:** Le frontend Next.js est exporté en build statique (`frontend/out/`) et servi par FastAPI à la racine `/` (StaticFiles). Un nouveau module `desktop/web_app.py` ouvre une fenêtre QWebEngineView pointant vers `http://127.0.0.1:8000`, détecte un serveur AXIOM existant (sinon démarre `uvicorn.Server` dans un thread daemon), et gère les écrans d'erreur. Le script console `axiom-desktop` est redirigé vers ce module.

**Tech Stack:** Python 3.14 (venv `backend/.venv`), PySide6 6.11 (QWebEngineView), FastAPI 0.141 + uvicorn, Next.js 16 (export statique), TypeScript.

## Global Constraints

- Pas de repo git dans `C:\Users\hp\Desktop\hakimagent` → toutes les étapes « Commit » sont à SKIPPER (ne pas exécuter `git add`/`git commit`).
- Windows / PowerShell 5.1 : ne jamais utiliser `&&` ; chaîner avec `;` et `if ($?) { ... }`.
- Le backend FastAPI existant doit rester inchangé pour `axiom-serve` (uvicorn séparé) — seules les ajouts compatibles sont autorisés dans `axiom/api/main.py` (aucun dans ce plan : le mount se fait dans `web_app.py`).
- La route racine JSON de l'API (`@app.get("/")`) doit céder la place au build statique uniquement dans le contexte de l'app native — pas pour le serveur seul.
- Build frontend : `output: 'export'` + `trailingSlash: true` conservé. Le build est 100 % client-side (vérifié : pas de routes API Next, pas de SSR, `API_BASE` défaut `http://localhost:8000`).
- Les tâches planifiées, la persistance (`axiom_state_v1`) et le trombone vivent côté client → fonctionnent dans la webview sans changement.
- Version : 4.0.0. Langue UI : français.
- Venv actif : `C:\Users\hp\Desktop\hakimagent\backend\.venv` (recréé récemment, `pip install -e .` déjà exécuté).

---

### Task 1: Build statique du frontend

**Files:**
- Modify: `C:\Users\hp\Desktop\hakimagent\frontend\next.config.ts`
- Create (résultat du build): `C:\Users\hp\Desktop\hakimagent\frontend\out\index.html`

**Interfaces:**
- Consumes: rien (frontend existant).
- Produces: dossier `frontend/out/` contenant le site statique (consommé par Task 2 via `find_build_dir()`).

- [ ] **Step 1: Activer l'export statique**

Modifier `frontend/next.config.ts` (contenu complet après modification) :

```ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  experimental: {
    // Turbopack désactivé car incompatible avec certains plugins Tailwind v4
  },
}

export default nextConfig
```

- [ ] **Step 2: Builder le frontend**

```powershell
cd C:\Users\hp\Desktop\hakimagent\frontend
npm run build
```

Attendu : build terminé sans erreur, dossier `out/` généré.

- [ ] **Step 3: Vérifier le build statique**

```powershell
Test-Path C:\Users\hp\Desktop\hakimagent\frontend\out\index.html
Get-ChildItem C:\Users\hp\Desktop\hakimagent\frontend\out -Recurse -File | Measure-Object | Select-Object Count
```

Attendu : `True`, plusieurs dizaines de fichiers (assets `_next/static`, index.html, 404.html…).

- [ ] **Step 4: Vérifier que le typecheck frontend passe toujours**

```powershell
cd C:\Users\hp\Desktop\hakimagent\frontend
npx tsc --noEmit
```

Attendu : sortie vide (code 0).

- [ ] **Step 5: Commit — SKIP (pas de repo git)**

---

### Task 2: Logique du backend embarqué (détection + démarrage)

**Files:**
- Create: `C:\Users\hp\Desktop\hakimagent\backend\desktop\web_app.py` (fonctions serveur uniquement ; la fenêtre arrive en Task 3)

**Interfaces:**
- Consumes: `axiom.api.main:app` (FastAPI existant, incluant routeur `/api/v1/*` et rate-limit) ; build statique `frontend/out/` (Task 1).
- Produces:
  - `find_build_dir() -> pathlib.Path | None`
  - `detect_axiom(host: str, port: int, timeout: float = 2.0) -> bool`
  - `ensure_backend(port: int = 8000, build_dir: pathlib.Path | None = None) -> tuple[bool, str]` — retourne `(ok, url_ou_message_erreur)`.

- [ ] **Step 1: Écrire le module (fonctions serveur)**

Créer `backend/desktop/web_app.py` avec le contenu suivant (la classe fenêtre sera ajoutée en Task 3 — le fichier final est montré en entier en Task 3) :

```python
import os
import threading
import time
from pathlib import Path

import httpx
from fastapi.staticfiles import StaticFiles
from uvicorn import Config, Server

from axiom.api.main import app as api_app

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
RETRY_ATTEMPTS = 10
RETRY_DELAY = 1.0

_WEBUI_MOUNTED = False


def find_build_dir() -> Path | None:
    """Résout le dossier du build statique frontend (frontend/out sous la racine du repo)."""
    override = os.environ.get("AXIOM_WEB_BUILD")
    if override:
        p = Path(override)
        return p if p.is_dir() else None
    repo_root = Path(__file__).resolve().parents[2]
    out = repo_root / "frontend" / "out"
    return out if out.is_dir() else None


def detect_axiom(host: str, port: int, timeout: float = 2.0) -> bool:
    """Vérifie qu'un serveur AXIOM répond déjà sur host:port."""
    try:
        r = httpx.get(f"http://{host}:{port}/api/v1/health", timeout=timeout)
        return r.json().get("agent") == "AXIOM"
    except Exception:
        return False


def _mount_webui(build_dir: Path) -> None:
    """Monte le build statique à la racine '/' de l'app FastAPI, une seule fois."""
    global _WEBUI_MOUNTED
    if _WEBUI_MOUNTED:
        return
    # Retire la route racine JSON existante pour que '/' serve le frontend
    api_app.routes = [
        r for r in api_app.routes if not (getattr(r, "path", None) == "/")
    ]
    api_app.mount("/", StaticFiles(directory=str(build_dir), html=True), name="webui")
    _WEBUI_MOUNTED = True


def _run_server(config: Config) -> None:
    Server(config).run()


def ensure_backend(port: int = DEFAULT_PORT, build_dir: Path | None = None) -> tuple[bool, str]:
    """Garantit un backend AXIOM joignable sur host:port.
    Si un serveur AXIOM répond déjà -> réutilisation. Sinon démarre uvicorn
    dans un thread daemon (et monte le build statique si fourni).
    Retourne (True, url) ou (False, message d'erreur).
    """
    if detect_axiom(HOST, port):
        return True, f"http://{HOST}:{port}"

    if build_dir is not None and build_dir.is_dir():
        try:
            _mount_webui(build_dir)
        except Exception as e:
            return False, f"Impossible de monter le frontend : {e}"

    config = Config("axiom.api.main:app", host=HOST, port=port, log_level="warning")
    thread = threading.Thread(target=_run_server, args=(config,), daemon=True)
    try:
        thread.start()
    except Exception as e:
        return False, f"Impossible de démarrer le serveur : {e}"

    for _ in range(RETRY_ATTEMPTS):
        if detect_axiom(HOST, port):
            return True, f"http://{HOST}:{port}"
        time.sleep(RETRY_DELAY)
    return False, "Le serveur n'a pas démarré correctement (port occupé ?)."
```

- [ ] **Step 2: Vérifier le module (import + compilation)**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe -m py_compile desktop\web_app.py
.\.venv\Scripts\python.exe -c "import desktop.web_app; print(desktop.web_app.find_build_dir())"
```

Attendu : compilation sans erreur ; le chemin de `frontend/out/` est imprimé (existe après Task 1).

- [ ] **Step 3: Vérifier la détection du serveur existant (port 8000 actuellement occupé par une instance AXIOM)**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe -c "from desktop.web_app import detect_axiom; print(detect_axiom('127.0.0.1', 8000))"
```

Attendu : `True` (l'instance lancée précédemment répond au health avec `agent: AXIOM`). Si `False`, vérifier qu'une instance tourne : `Invoke-RestMethod http://127.0.0.1:8000/api/v1/health`.

- [ ] **Step 4: Vérifier le démarrage embarqué sur un port libre + service du build statique**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe -c "from desktop.web_app import find_build_dir, ensure_backend; ok, url = ensure_backend(port=8003, build_dir=find_build_dir()); print(ok, url); import httpx; h = httpx.get(url + '/api/v1/health', timeout=5); print('health:', h.json()); r = httpx.get(url + '/', timeout=5); print('root:', r.status_code, r.text[:80])"
```

Attendu : `True http://127.0.0.1:8003`, `health: {'status': 'ok', ...}` et `root: 200` avec début du HTML (`<!DOCTYPE html>` ou `<!doctype html>`). Le thread daemon s'arrêtera avec le processus.

- [ ] **Step 5: Commit — SKIP (pas de repo git)**

---

### Task 3: Fenêtre Qt + intégration du script `axiom-desktop`

**Files:**
- Modify: `C:\Users\hp\Desktop\hakimagent\backend\desktop\web_app.py` (ajout de la classe fenêtre + main)
- Modify: `C:\Users\hp\Desktop\hakimagent\backend\pyproject.toml` (ligne `axiom-desktop`)

**Interfaces:**
- Consumes: fonctions de Task 2 (`ensure_backend`, `find_build_dir`, `HOST`, `DEFAULT_PORT`) ; `desktop.main` (ancienne app Qt, inchangée, accessible via `python -m desktop.main`).
- Produces: script console `axiom-desktop` → `desktop.web_app:main`.

- [ ] **Step 1: Ajouter la fenêtre Qt et main() à `web_app.py`**

Ajouter au fichier existant (Task 2) le contenu suivant :

```python
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget


class WebAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AXIOM v4.0.0")
        self.resize(1280, 800)
        self._dev_mode = os.environ.get("AXIOM_DEV") == "1"
        self._error_box = None
        self.browser = None
        self.retry_button = None
        self._central = QWidget()
        self.setCentralWidget(self._central)
        self._retry()

    # ---- Gestion des erreurs ----

    def _show_error(self, title: str, message: str) -> None:
        if self.browser is not None:
            self.browser.deleteLater()
            self.browser = None
        if self._error_box is None:
            layout = QVBoxLayout(self._central)
            label = QLabel(title)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 22px; font-weight: bold; padding: 16px;")
            detail = QLabel(message)
            detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
            detail.setWordWrap(True)
            detail.setStyleSheet("font-size: 13px; color: #888; padding: 0 32px 16px;")
            self.retry_button = QPushButton("Réessayer")
            self.retry_button.clicked.connect(self._retry)
            layout.addStretch()
            layout.addWidget(label)
            layout.addWidget(detail)
            layout.addWidget(self.retry_button)
            layout.addStretch()
            self._error_box = layout
        title_label = self._error_box.itemAt(1).widget()
        detail_label = self._error_box.itemAt(2).widget()
        title_label.setText(title)
        detail_label.setText(message)
        self._error_box.itemAt(3).widget().show()

    def _show_browser(self, url: str) -> None:
        if self._error_box is not None:
            for i in range(self._error_box.count()):
                self._error_box.itemAt(i).widget().hide()
        if self.browser is None:
            self.browser = QWebEngineView(self._central)
            layout = QHBoxLayout(self._central)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.browser)
            self.browser.loadProgress.connect(self._on_progress)
            self.browser.loadFinished.connect(self._on_loaded)
        self.browser.load(QUrl(url))

    def _on_progress(self, progress: int) -> None:
        if progress < 100:
            self.setWindowTitle(f"AXIOM — chargement {progress}%")

    def _on_loaded(self, ok: bool) -> None:
        self.setWindowTitle("AXIOM v4.0.0")

    # ---- Démarrage ----

    def _retry(self) -> None:
        try:
            if self._dev_mode:
                self._show_browser("http://localhost:3000")
                return
            build_dir = find_build_dir()
            if build_dir is None:
                self._show_error(
                    "Build introuvable",
                    "Le frontend n'est pas compilé.\nLancez `npm run build` dans le dossier frontend/.",
                )
                return
            ok, result = ensure_backend(DEFAULT_PORT, build_dir)
            if ok:
                self._show_browser(result)
            else:
                self._show_error("Démarrage impossible", result)
        except Exception as e:
            self._show_error("Erreur inattendue", str(e))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AXIOM")
    app.setApplicationVersion("4.0.0")
    app.setOrganizationName("AXIOM")
    window = WebAppWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rediriger le script console**

Dans `backend/pyproject.toml`, remplacer la ligne :

```toml
axiom-desktop = "desktop.main:main"
```

par :

```toml
axiom-desktop = "desktop.web_app:main"
```

- [ ] **Step 3: Réinstaller le package pour régénérer l'entrée console**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe -m pip install -e . 2>&1 | Select-Object -Last 1
```

Attendu : `Successfully installed axiom-4.0.0` (ou message équivalent).

- [ ] **Step 4: Vérifier l'import et l'existence du script**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe -m py_compile desktop\web_app.py
Test-Path .\.venv\Scripts\axiom-desktop.exe
.\.venv\Scripts\python.exe -c "from desktop.web_app import WebAppWindow, main; print('import_ok')"
```

Attendu : compilation OK, `True`, `import_ok`.

- [ ] **Step 5: Test de lancement de la fenêtre (manuel)**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\axiom-desktop.exe
```

Attendu : une fenêtre « AXIOM v4.0.0 » (1280×800) s'ouvre et affiche l'interface AXIOM (frontend statique servi par le backend embarqué — le serveur déjà actif sur 8000 est détecté et réutilisé). Fermer la fenêtre → processus terminé. Si la fenêtre ne s'ouvre pas ou reste noire : relever l'erreur affichée et la rapporter.

- [ ] **Step 6: Commit — SKIP (pas de repo git)**

---

### Task 4: Vérification de bout en bout

**Files:**
- Aucun (vérifications manuelles).

**Interfaces:**
- Consumes: l'app complète (Tasks 1-3).

- [ ] **Step 1: Discuter avec l'agent dans la fenêtre native**

Ouvrir l'app (`axiom-desktop`), envoyer un message (ex. « Bonjour, présente-toi en une phrase »). Attendu : réponse réelle de l'agent (clé OpenRouter configurée — `openrouter_configured: true` confirmé au health).

- [ ] **Step 2: Trombone**

Joindre un petit fichier texte (.txt) via le trombone → chip `📎 nom · taille Ko` au-dessus de la barre, envoi → badge `📎 nom` sous le message utilisateur, l'agent reçoit le contenu (réponse cohérente avec le contenu du fichier). Joindre un .exe → toast « Type de fichier non supporté ».

- [ ] **Step 3: Persistance**

Fermer l'app, la rouvrir → la conversation est restaurée (localStorage). Supprimer une conversation via la corbeille dans l'Historique → toast « Conversation supprimée ».

- [ ] **Step 4: Tâches planifiées**

Créer une tâche planifiée dans le panneau → fermer/rouvrir l'app → tâche toujours présente.

- [ ] **Step 5: Cas de réutilisation du port**

Avec une instance AXIOM qui tourne sur 8000, lancer `axiom-desktop` → aucune erreur de bind, l'app se connecte au serveur existant (pas de second serveur).

- [ ] **Step 6: Vérifier que le serveur seul reste fonctionnel**

```powershell
cd C:\Users\hp\Desktop\hakimagent\backend
.\.venv\Scripts\python.exe -c "import httpx; r = httpx.get('http://127.0.0.1:8000/api/v1/health', timeout=5); print(r.json())"
```

Attendu : `{'status': 'ok', 'agent': 'AXIOM', ...}` (l'API serveur seule n'est pas affectée par le mount, car celui-ci n'a lieu que dans `ensure_backend`).

- [ ] **Step 7: Commit — SKIP (pas de repo git)**

---

## Self-Review

**1. Couverture de la spec :**
- Build statique (spec §1) → Task 1 ✓
- Fenêtre + serveur embarqué, détection, retries, écrans d'erreur, mode dev `AXIOM_DEV` (spec §2) → Tasks 2-3 ✓
- Chemin du build + override `AXIOM_WEB_BUILD` (spec §2) → Task 2 `find_build_dir` ✓
- Script console `axiom-desktop` redirigé, ancienne app conservée via `python -m desktop.main` (spec §3) → Task 3 ✓
- Aucune nouvelle dépendance (spec §3) → vérifié : httpx/PySide6/fastapi déjà dans les deps ✓
- Erreurs et cas limites (tableau spec) → `ensure_backend` (port occupé par AXIOM → réutilisation ; port occupé par autre → message d'échec après 10 essais), écrans d'erreur + bouton Réessayer (Task 3), build absent (Task 3) ✓
- Tests manuels (spec §Tests) → Task 4 ✓
- Hors périmètre (PyInstaller, installer, tray…) → absent du plan ✓

**2. Placeholder scan :** aucun TBD/TODO ; tout le code est fourni ; les vérifications attendues sont explicites. ✓

**3. Cohérence des types/noms :** `find_build_dir() -> Path | None`, `detect_axiom(host, port, timeout) -> bool`, `ensure_backend(port, build_dir) -> tuple[bool, str]`, `HOST`, `DEFAULT_PORT`, `WebAppWindow`, `main()` — définis en Task 2 et consommés à l'identique en Tasks 3-4. ✓

**Note :** le fichier `desktop/web_app.py` est créé en Task 2 (fonctions serveur) puis complété en Task 3 (fenêtre). L'import de la fenêtre au top du module dans `main()` ne s'exécute qu'à l'appel — le `py_compile` de Task 2 ne dépend pas de PySide6.
