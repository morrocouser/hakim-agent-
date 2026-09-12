# Spec — Intégration 21st.dev : recherche de composants UI pour AXIOM

Date : 2026-08-03
Statut : validée (brainstorming, 3 sections approuvées par l'utilisateur)

## 1. Objectif

L'agent AXIOM recherche automatiquement des composants UI dans le catalogue
21st.dev quand la tâche est frontend, et injecte les métadonnées + le code des
meilleurs résultats (jusqu'à 3) dans le contexte de l'agent CODER — sans
tool-calling réel, selon le même mécanisme que la recherche web en mode
RECHERCHE.

## 2. API 21st.dev (source)

- Endpoint : `https://21st.dev/api/mcp` — HTTP, JSON-RPC 2.0
- Auth : header `x-api-key` (clé de https://21st.dev/settings/api-keys)
- Méthodes utilisées : `tools/call` avec `name: "search"` (gratuit, métadonnées)
  et `name: "get_component"` (code ; gratuit sur plans payants, compté sur le
  plan gratuit)
- Paramètres `search` : `query`, `type` (`component`/`theme`/`template`/`all`),
  `limit`, `free` (booléen) — seuls `query`, `type`, `limit` sont utilisés ici
- Réponse MCP : `result.content` (blocs texte) + éventuel `result.isError`

## 3. Configuration (.env)

Nouvelle variable dans `backend/.env` (déjà renseignée) :

| Variable | Valeur | Rôle |
|---|---|---|
| `API_KEY_21ST` | clé fournie par l'utilisateur | Clé API 21st.dev ; vide = outil inactif |

## 4. Nouveau fichier — `backend/axiom/tools/component_search.py`

Calqué sur le pattern `WebSearchTool` (`backend/axiom/tools/web_search.py`).

### 4.1 `is_frontend_task(description: str) -> bool`

Fonction pure, regex word-boundary (même esprit que `scoring.py` ligne 95-99).
Mots-clés : `react, tailwind, ui, composant, component, page, interface,
navbar, hero, pricing, dashboard, frontend, landing, web page`.

### 4.2 `ComponentSearchTool`

- `__init__(api_key: Optional[str] = None)` — `self.api_key = api_key or ""`,
  client `httpx.AsyncClient(timeout=30)`
- `_rpc_call(name: str, arguments: dict) -> dict` — POST JSON-RPC 2.0 sur
  `https://21st.dev/api/mcp`, headers `x-api-key` + `Content-Type:
  application/json`, corps `{"jsonrpc": "2.0", "id": 1, "method":
  "tools/call", "params": {"name": name, "arguments": arguments}}`.
  Retourne `result` ; lève/convertit en erreur si `result.isError` ou si la
  réponse est mal formée
- `search(query: str, limit: int = 5, item_type: str = "component") -> str` —
  texte formaté des métadonnées : titre, description, preview URL, id
- `get_component(item_id: str) -> str` — code du composant (texte brut du
  bloc `result.content`)
- `search_with_code(query: str, limit: int = 3) -> str` — combine `search()`
  puis `get_component()` sur les ids des `limit` premiers résultats (ou moins
  si la recherche en retourne moins) ; résultat structuré (métadonnées +
  section CODE pour chaque composant)
- `close()` — ferme le client http

### 4.3 Gestion d'erreurs (jamais levée vers le loop)

- Sans clé : `"[Recherche composants indisponible]\nConfigure API_KEY_21ST
  dans .env pour activer la recherche de composants."`
- Erreur API (timeout, 401, quota, `isError`) : `"[Erreur recherche
  composants] <message>"` — le ReActLoop ne plante jamais à cause de cet outil

## 5. Modifications — `backend/axiom/core/react_loop.py`

- `__init__` (ligne 26, après web_search) :
  `self.component_search = ComponentSearchTool(os.getenv("API_KEY_21ST", ""))`
- `execute()` : à côté du bloc web search (lignes 44-48), si
  `is_frontend_task(task.description)` →
  `context = f"{context}\n\n[COMPOSANTS 21ST.DEV]:\n{results}"` avec
  `results = await self.component_search.search_with_code(task.description)`

## 6. Vérification (tests)

- `pytest` ajouté à `backend/requirements.txt`
- Nouveau fichier `backend/tests/test_component_search.py` :
  1. `test_is_frontend_task` — positifs (`"créer une page react"`,
     `"navbar tailwind"`) et négatifs (`"analyse SQL"`, `"email marketing"`)
  2. `test_search_with_code_no_key` — sans clé → message indisponible
  3. `test_search_formats_results` — réponse JSON-RPC mockée
     (`httpx.MockTransport`) → métadonnées formatées
  4. `test_get_component_returns_code` — mock `tools/call` `get_component` →
     code retourné
- Exécution : `pytest backend/tests/`

## 7. Hors périmètre

- Endpoint `/tools/21st` (interrogation manuelle du catalogue) : non inclus
  (YAGNI), ajouté plus tard si besoin
- `search_logo` / génération 21st AI (`generate`...) : non inclus, coûtent
  des crédits ou hors besoin
- Pas de repo git → pas de commit
