# Spec — Rebranding AXIOM → APEX avec logos

Date : 2026-08-03
Statut : validée (brainstorming, design approuvé)

## 1. Objectif

Renommer la marque visible « AXIOM » en « APEX » et intégrer les logos fournis
(`apex-icon-192.png`, `apex-icon-512.png`, `apex-icon-favicon.png`,
`apex-icon.svg`, à la racine de `C:\Users\hp\Desktop\hakimagent`). La fenêtre
de l'app native affiche le nom « APEX » avec l'icône, à la manière de l'app
Claude (barre de titre : icône + nom).

Le package Python interne (`axiom`), les scripts (`axiom`, `axiom-tui`,
`axiom-serve`, `axiom-desktop`), le nom de package `axiom-4.0.0` dans
`pyproject.toml` et la clé localStorage `axiom_state_v1` sont **conservés**
(renommage de marque uniquement, zéro casse).

## 2. Modifications

### 2.1 Backend — `backend/desktop/web_app.py` (fenêtre Qt)

- `setWindowTitle("APEX")` (titre fixe, comme Claude — plus de « AXIOM v4.0.0 » ;
  le titre de chargement devient « APEX — chargement N% »).
- `app.setApplicationName("APEX")` ; `app.setApplicationVersion("4.0.0")` conservé.
- Icône fenêtre + taskbar : `QIcon(Path(__file__).parent / "resources" / "apex-icon.png")`
  appliqué à la fenêtre ET à l'application.
- `detect_axiom()` : comparaison `health["agent"] == "APEX"` (cohérent avec le
  health renommé).

### 2.2 Ressource logo — `backend/desktop/resources/`

Copie de `apex-icon-192.png` → `backend/desktop/resources/apex-icon.png`
(les 4 fichiers source restent à la racine du projet ; seule la copie PNG 192
est embarquée pour la fenêtre Qt — taille adaptée à un icône de fenêtre).

### 2.3 Backend — API et client LLM

- `backend/axiom/api/routes.py` : health → `"agent": "APEX"` (et message 503
  générique déjà prévu par la spec opencode-models).
- `backend/axiom/claude/client.py` : `APP_TITLE = "APEX v4.0 Orchestrateur"`.
  `APP_REFERRER = "https://github.com/hakimagent/axiom"` conservé.
- `backend/axiom/core/system_prompt.py` : « Tu es AXIOM, un agent IA
  orchestrateur... » → « Tu es APEX, un agent IA orchestrateur... » (première
  phrase uniquement, le reste du prompt inchangé).
- TUI (`cli/tui/app.py`, headers, help screen) et ancienne app desktop
  (`desktop/main_window.py`, `main.py`) : titres et mentions visibles « AXIOM »
  → « APEX » (sans toucher aux identifiants internes).

### 2.4 Frontend

- `frontend/app/layout.tsx` : metadata `title: "APEX"` (et description).
- `frontend/app/icon.png` : copie de `apex-icon-favicon.png` (favicon auto de
  Next 16 — présente dans le build statique `out/`).
- `frontend/public/apex-icon-192.png` : copie pour affichage dans le sidebar.
- Sidebar / pages : texte « AXIOM » visible → « APEX » ; le sidebar affiche le
  logo (img `apex-icon-192.png`) + « APEX » à la manière de l'app Claude.
- Clé localStorage `axiom_state_v1` conservée (pas de perte de conversations).
- Rebuild : `npm run build` (régénère `out/`) + `npx tsc --noEmit` (code 0).

### 2.5 Hors périmètre

- Pas de renommage des modules Python / scripts / package.
- Pas de modification des docs (specs/plans) ni du `.env`.
- Pas de repo git → pas de commit.

## 3. Vérification

1. `npm run build` + `npx tsc --noEmit` OK.
2. `axiom-desktop` : fenêtre titre « APEX » avec icône visible (barre de titre
   + taskbar), page chargée affichant logo + « APEX ».
3. `GET /api/v1/health` → `"agent": "APEX"`.
4. `find_build_dir()` + `ensure_backend` : `detect_axiom` valide la connexion
   avec le health renommé (aucune erreur au lancement).
