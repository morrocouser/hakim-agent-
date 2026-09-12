# Persistance des conversations (localStorage) — Design

> Date : 2026-08-02 · Scope : frontend uniquement · Pas de repo git (pas de commit)

## Goal

Enregistrer automatiquement les conversations et les tâches planifiées d'AXIOM dans `localStorage` : au rechargement de la page, l'historique complet est restauré, la dernière conversation ouverte est rouverte, et un bouton corbeille permet de supprimer définitivement une conversation.

## Contexte

- `frontend/app/page.tsx` : les états `sessions` (ConversationSession[]), `tasks` (ScheduledTask[]) et `currentId` sont en mémoire (`useState`) — tout est perdu au rechargement. Deux conversations de démonstration (s1/s2) sont pré-chargées dans l'état initial.
- Aucune persistance de conversations n'existe (seul le thème utilise localStorage : `axiom_theme` dans `lib/theme.ts`).
- Backend : stateless, aucune base de données, aucune route de persistance — hors périmètre.

## Approche retenue

Module de persistance dédié `frontend/lib/storage.ts` + types partagés `frontend/lib/types.ts` + hydratation/écriture dans `page.tsx`. Une seule clé localStorage versionnée (`axiom_state_v1`) contenant l'état complet (écriture atomique). Hydratation après montage (pattern ThemeProvider → aucun mismatch SSR/hydration).

## Architecture

### `frontend/lib/types.ts` (nouveau)

Extrait les interfaces actuellement déclarées dans `page.tsx` :

- `Message` (avec `file?: string`, utilisé par la fonctionnalité trombone)
- `ConversationSession`
- `ScheduledTask`
- `Toast`

`page.tsx` les importe depuis `types.ts` ; aucun autre changement de forme des types.

### `frontend/lib/storage.ts` (nouveau)

```ts
export interface AxiomState {
  version: 1
  sessions: ConversationSession[]
  tasks: ScheduledTask[]
  activeSessionId: string | null
}
```

- `STORAGE_KEY = 'axiom_state_v1'` (versionné → migration future possible).
- `loadState(): AxiomState` — lecture + `JSON.parse` protégé (try/catch) ; clé absente, JSON invalide ou `version` inconnue → état vide (`sessions: []`, `tasks: []`, `activeSessionId: null`) — les conversations de démo sont retirées.
- `saveState(state: AxiomState): boolean` — écriture atomique de l'objet entier ; retourne `false` uniquement si l'écriture échoue alors que localStorage est disponible (ex. quota dépassé), sans lever d'exception. Si localStorage est indisponible (détecté par `isStorageAvailable()`, vérifié à la lecture), `saveState` retourne `true` sans rien écrire (no-op silencieux).
- `isStorageAvailable(): boolean` — accès try/catch à `window.localStorage`.

### `frontend/app/page.tsx`

- **État initial** : `sessions: []`, `tasks: []`, `currentId` null → les démos s1/s2 sont supprimées. `currentId` initial : null (la vue chat affiche l'état vide en attendant l'hydratation).
- **Hydratation** : `useEffect` exécuté une seule fois côté client — `loadState()` puis :
  - si `activeSessionId` existe dans la liste → `setCurrentId(id)` + `setMessages(messages de la session)` (dernière conversation rouverte avec son fil) ;
  - sinon → `currentId` de la première session, liste vide → conversation vide.
- **Écriture automatique** : `useEffect` sur `[sessions, tasks, currentId]` → `saveState({ version: 1, sessions, tasks, activeSessionId: currentId })` ; si l'écriture échoue → toast `error` « Stockage local plein — conversation non enregistrée ».
- **`selectSession`** : met à jour `currentId` (persisté par l'effet).
- **`newConversation`** : la nouvelle session est ajoutée à `sessions` et `currentId` bascule (persisté par l'effet — une conversation neuve sans message est donc sauvegardée).

## Suppression (corbeille)

- Vue Historique : bouton corbeille (icône) sur chaque ligne de conversation → suppression directe de `sessions` + toast « Conversation supprimée » (pas de confirmation).
- Si la conversation supprimée est celle ouverte (`currentId`) → `newConversation()` (bascule sur une nouvelle conversation vide).
- Persisté par l'effet d'écriture.

## Gestion d'erreurs

| Situation | Comportement |
|---|---|
| Quota dépassé | `saveState` → `false` → toast « Stockage local plein — conversation non enregistrée » ; app fonctionne en mémoire |
| localStorage indisponible (mode privé) | `isStorageAvailable()` → `false` → `loadState` retourne l'état vide, `saveState` no-op silencieux (aucun toast) |
| JSON corrompu / version inconnue | État vide + reconstruction propre ; aucune exception propagée au composant |

## Rendu avec `currentId` initial

`currentId` passe en `string | null` : au rendu, la comparaison `s.id === currentId` reste valide avec `null` (aucune session active). Le plan d'implémentation doit vérifier tous les usages de `currentId` (ex. `sessions.find(...)`, map) pour garantir la compatibilité avec `null` avant hydratation.

## Hors périmètre

- Backend / base de données / routes de persistance (aucun changement).
- Suppression de tâches planifiées (non demandée).
- Renommage de conversations.
- Migration de données existantes (clé créée au premier lancement).

## Tests

- `npx tsc --noEmit` + `npm run lint` dans `frontend/` (pas de framework de test frontend).
- Test manuel navigateur :
  1. Envoyer un message → recharger → conversation rouverte avec son fil (agent, score, durée, badge fichier si joint).
  2. Créer une tâche → recharger → tâche toujours présente.
  3. Corbeille sur une conversation → recharger → absente de l'historique ; si c'était la conversation ouverte → nouvelle conversation vide affichée.
  4. Nouvelle conversation sans message → recharger → présente dans l'historique.
  5. Premier lancement (localStorage vide) → historique vide, aucune démo.
