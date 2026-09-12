# Spec — Connexion des modèles opencode à l'agent AXIOM

Date : 2026-08-03
Statut : validée (brainstorming, 2 sections approuvées par l'utilisateur)

## 1. Objectif

AXIOM appelle désormais par défaut la passerelle d'inférence Console opencode
(`https://console.opencode.ai/inference/openai/v1`, endpoint OpenAI-compatible)
avec le modèle gratuit `opencode/deepseek-v4-flash-free`, **sans clé API**.
OpenRouter reste utilisable en réglant deux variables d'environnement.

## 2. Configuration (.env) — nouvelle source de vérité

| Variable | Défaut | Rôle |
|---|---|---|
| `AXIOM_LLM_BASE_URL` | `https://console.opencode.ai/inference/openai/v1` | Base URL OpenAI-compatible du fournisseur LLM |
| `AXIOM_LLM_MODEL` | `opencode/deepseek-v4-flash-free` | ID de modèle unique, écrase tous les paliers |
| `AXIOM_LLM_API_KEY` | vide | Clé API du fournisseur ; vide = modèles gratuits (pas de header `Authorization`) |

- `.env` du projet : `AXIOM_LLM_BASE_URL` et `AXIOM_LLM_MODEL` renseignés,
  `AXIOM_LLM_API_KEY` vide. `OPENROUTER_API_KEY` reste en place mais n'est
  utilisée **que** si la base URL est OpenRouter.
- Variables existantes préservées : `OPENROUTER_API_KEY` (repli OpenRouter),
  `OPENCHASSIS_API_BASE` (repli local explicite, priorité après `AXIOM_LLM_BASE_URL`).

## 3. Modifications — `backend/axiom/claude/client.py`

### 3.1 Résolution de la base URL (`__init__`)
Priorité : `AXIOM_LLM_BASE_URL` (env) > `OPENCHASSIS_API_BASE` (env, repli local
explicite) > défaut passerelle Console opencode. Suppression de la sélection
« OpenRouter si clé, sinon OpenChassis » : la base ne dépend plus de la clé.

### 3.2 Résolution de la clé API (`__init__`)
1. `AXIOM_LLM_API_KEY` si non vide ;
2. sinon `OPENROUTER_API_KEY` **uniquement si** la base URL contient
   `openrouter.ai` ;
3. sinon pas de clé.

Le header `Authorization: Bearer <key>` n'est ajouté que si une clé existe.
Les headers `HTTP-Referer` / `X-Title` restent envoyés (ignorés par les
passerelles autres qu'OpenRouter).

### 3.3 Surcharge du modèle (`chat()`)
`model = os.getenv("AXIOM_LLM_MODEL") or model`. Si `AXIOM_LLM_MODEL` absent ET
base = OpenRouter → les IDs de paliers (`ModelName.BEST/LARGE/...`) passent
inchangés (comportement actuel).

### 3.4 `is_configured()`
Vrai si une clé existe OU si la base n'est pas le repli local OpenChassis
(la passerelle gratuite n'exige pas de clé). Le repli « simulation »
(`_mock_response`) n'est atteint que si base = OpenChassis local.

## 4. Modifications — `backend/axiom/api/routes.py`

- `/health` : ajout de `"llm_provider"` (`opencode-console` si base contient
  `console.opencode.ai` ; `openrouter` si base contient `openrouter.ai` ;
  `openchassis` si repli local ; sinon `custom`) et `"llm_model"` (modèle
  effectif, i.e. `AXIOM_LLM_MODEL` ou palier par défaut). `openrouter_configured`
  conservé (valeur = `is_configured()`) pour compatibilité frontend.
- Messages d'erreur 503 génériques : « LLM not configured. Vérifiez
  AXIOM_LLM_BASE_URL et AXIOM_LLM_API_KEY dans .env » (remplace « OpenRouter
  not configured. Set OPENROUTER_API_KEY »).

## 5. Vérification (tests)

1. `GET https://console.opencode.ai/inference/openai/v1/models` (sans clé) :
   `opencode/deepseek-v4-flash-free` présent.
2. Serveur AXIOM sur port de test → `/api/v1/health` : `llm_provider =
   "opencode-console"`, `llm_model = "opencode/deepseek-v4-flash-free"`.
3. `POST /api/v1/chat` réel (message simple) : réponse du modèle via la
   passerelle, sans clé envoyée.
4. Régression : `AXIOM_LLM_BASE_URL=https://openrouter.ai/api/v1` (+ clé
   OpenRouter) → une requête `/chat` répond via OpenRouter.

## 6. Hors périmètre

- Bug rate limiter 429→500 (découvert en Task 4 du plan app-native) : suivi
  séparé, non traité ici.
- Checklist manuelle app-native (chat réel, trombone, persistance, tâches) :
  toujours en attente, exécutée après cette feature.
- Pas de repo git → pas de commit.
