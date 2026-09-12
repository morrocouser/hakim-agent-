# App Native AXIOM — Fenêtre Qt + Backend embarqué

Date : 2026-08-03
Statut : Validé (brainstorming)
Contexte : l'utilisateur ne veut plus démarrer le backend (uvicorn port 8000) et le frontend (Next.js port 3000) séparément.

## Objectif

Une seule commande `axiom-desktop` lance une fenêtre native (PySide6, QWebEngineView) qui affiche le frontend web AXIOM existant, avec le backend FastAPI démarré automatiquement dans un thread invisible au sein du même processus. Aucun process ni terminal supplémentaire.

## Architecture

```
Processus unique (script axiom-desktop)
│
├─ Fenêtre PySide6 (QWebEngineView, Chromium embarqué)
│    └─ charge http://127.0.0.1:8000  (frontend statique servi par FastAPI)
│
└─ Thread daemon : uvicorn.Server (app FastAPI axiom.api.main:app)
     ├─ routes API /api/v1/* (chat, execute, health, memory…)
     └─ StaticFiles "/" → build statique Next.js (frontend/out)
```

- Frontend servi à la racine `/` par FastAPI (`StaticFiles(html=True)`), API sur le même origin → aucun changement CORS nécessaire pour l'app.
- Les routes CORS existantes (`localhost:3000`) restent pour le mode dev.
- Rate-limit existant (60 req/min/IP) inchangé.

## Composants

### 1. Build statique du frontend (`frontend/next.config.ts`)

- Activer `output: 'export'` (+ conserver `trailingSlash: true`).
- `npm run build` → `frontend/out/` (HTML/JS/CSS purs).
- Compatibilité vérifiée : la page est 100 % client-side (`'use client'`), aucune route API Next, aucune dépendance SSR. `lib/api.ts` pointe vers `http://localhost:8000` (défaut `API_BASE`) → fonctionne tel quel depuis le build exporté.
- La persistance (localStorage, clé `axiom_state_v1`), le trombone et les tâches planifiées fonctionnent dans la webview comme dans un navigateur.

### 2. Fenêtre + serveur embarqué (`backend/desktop/web_app.py`, nouveau)

Classe `NativeWindow` (QMainWindow) :
- `QWebEngineView` 1280×800, titre « AXIOM », titre de version « AXIOM v4.0.0 ».
- Séquence de démarrage : détecter un serveur AXIOM existant (GET `/api/v1/health` → `agent == "AXIOM"`) ; si présent → s'y connecter (cas : instance déjà lancée, port 8000 occupé par AXIOM). Sinon → démarrer `uvicorn.Server` (Config host `127.0.0.1`, port 8000, `log_level="warning"`) dans un thread daemon ; attendre le health OK avec retries avant de charger la page.
- Échec : port occupé par un autre service, ou backend injoignable après N tentatives (N=10, délai 1 s) → écran d'erreur dans la fenêtre avec message explicite + bouton « Réessayer ».
- Build statique absent (`frontend/out/` introuvable depuis le repo) → écran d'erreur : « Build introuvable — lancez `npm run build` dans frontend/ ».
- Mode dev : variable d'environnement `AXIOM_DEV=1` → charge `http://localhost:3000` au lieu de 8000 (sans serveur embarqué).
- Fermeture : thread daemon → le processus se termine proprement avec la fenêtre.
- Optionnel non implémenté (YAGNI) : icône personnalisée, menu, réglages de fenêtre persistants.

Fonction `main()` : crée `QApplication`, applique les styles par défaut, affiche la fenêtre, `sys.exit(app.exec())`.

Résolution du chemin du build : depuis `backend/desktop/`, remonter de 2 niveaux → racine du repo, puis `frontend/out`. Variable d'environnement `AXIOM_WEB_BUILD` pour surcharger le chemin.

### 3. Script console (`backend/pyproject.toml`)

- Changer `axiom-desktop = "desktop.main:main"` → `axiom-desktop = "desktop.web_app:main"`.
- L'ancienne app Qt autonome reste lançable : `python -m desktop.main`. L'app TUI (`axiom-tui`) et le serveur (`axiom-serve`) inchangés.
- Aucune nouvelle dépendance Python (PySide6 déjà présent).

## Erreurs et cas limites

| Cas | Comportement |
|---|---|
| Port 8000 libre | Thread uvicorn démarré par l'app |
| Port 8000 occupé par AXIOM (health OK) | Connexion directe, pas de second serveur |
| Port 8000 occupé par autre service | Écran d'erreur + bouton Réessayer |
| `frontend/out/` absent | Écran d'erreur : lancer `npm run build` |
| Backend injoignable après 10 essais | Écran d'erreur + bouton Réessayer |
| Fermeture de la fenêtre | Thread daemon, processus se termine |

## Tests (manuel)

1. `npm run build` dans `frontend/` → `frontend/out/` généré.
2. `axiom-desktop` → fenêtre ouverte, page AXIOM affichée, santé backend OK dans l'API (health endpoint).
3. Envoyer un message → réponse réelle de l'agent (OpenRouter).
4. Joindre un fichier via le trombone → contenu injecté, badge affiché.
5. Fermer/rouvrir l'app → conversation restaurée (localStorage).
6. Corbeille d'historique fonctionnelle.
7. Cas : instance déjà lancée sur 8000 → l'app s'y connecte sans erreur (testé en gardant le serveur actuel actif).

## Hors périmètre (YAGNI)

- .exe autonome (PyInstaller) — éventuel second temps.
- Installation Windows (installateur).
- Synchronisation multi-fenêtres.
- Raccourcis globaux, tray icon, mises à jour auto.
