# Suivi des correctifs de sécurité

Dernière mise à jour : revue de code de la branche `claude/practical-hamilton-e35343`.
« Vérifié » = relu dans le code et couvert par un test ou une lecture directe.

## Corrigé et vérifié

| Sujet | Correctif | Où |
|---|---|---|
| Jetons JWT | Un refresh token n'est plus accepté comme access token ; rotation du refresh, révocation au logout (table `revoked_tokens`) | `backend/axiom/auth/jwt.py`, `api/auth_routes.py` |
| IDOR `/chat` | La conversation doit appartenir à l'utilisateur | `backend/axiom/api/routes.py` |
| Routes sans auth | `/execute`, `/chat/stream`, `/memory`, `/errors` exigent une connexion ; écritures mémoire/erreurs réservées aux admins | `api/routes.py` |
| Exécution de commandes | Commandes lançant un processus réservées aux admins (`HAKIM_ADMIN_USERS`) ; interpréteurs retirés de la liste blanche ; options git/gh dangereuses refusées | `commands/handlers.py` |
| Outil bash / CLI | Refus par défaut sans confirmation utilisateur ; garde-fou normalisé (best-effort) | `cli_engine.py`, `tools/builtin.py` |
| Rate limiting | Couvre `/api/*` et `/auth/*` ; quota strict (5 / 5 min) sur login/register/refresh ; user-agent exclu de la clé | `api/main.py` |
| Sandbox Docker | `--read-only`, `--cap-drop ALL`, `no-new-privileges`, `--pids-limit`, utilisateur non-root, code monté en `:ro`, pas de swap, images surchargeables par digest | `tools/code_executor.py` |
| Path traversal fichiers | `_resolve_safe_path` (`resolve()` + `relative_to()`) | `tools/file_manager.py` |
| Commit git | Le message est un seul argument (plus de découpage sur les espaces) | `commands/handlers.py` |
| Permissions de config | Dossier `~/.axiom` en `0700` (il était en `0600`, donc inaccessible) et fichier en `0600` | `backend/cli/tui/config.py` |

Tests : `backend/tests/test_auth_hardening.py`.

## Reste à faire

- **Mémoire globale** : `GET /api/v1/memory` est lisible par tout compte connecté alors que l'inscription est ouverte → mémoire par utilisateur ou lecture réservée aux admins.
- **Inscription ouverte** : mot de passe minimum de 6 caractères, pas de vérification d'e-mail.
- **Sandbox** : figer les images Docker par digest en production (`HAKIM_SANDBOX_IMAGE_*`).
- **Désérialisation / divulgation** : revoir les messages d'erreur renvoyés par l'API (`str(e)` dans plusieurs routes).
- **Dates** : remplacer `datetime.utcnow()` (déprécié).

## Points non revérifiés (hérités de l'ancien suivi)

HTTPS `verify=True` et timeouts dans `backend/cli/main.py`, validation de clé API, variable `SPEC` de `axiom.spec`, nettoyage des erreurs côté desktop : présents dans le code lu, sans test dédié.

## Dette d'architecture

- `AXIOM_v4_MEGA_PROMPT.md` : fichier de documentation très volumineux (plus de 46 000 lignes).
- `commands/registry.py` (1500+ lignes) et `frontend/components/ui/ai-prompt-input.tsx` (2600+ lignes) à découper.
