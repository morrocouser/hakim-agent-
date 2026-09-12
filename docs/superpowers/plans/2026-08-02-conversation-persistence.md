# Persistance des conversations (localStorage) — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enregistrer automatiquement conversations et tâches dans `localStorage` (clé unique versionnée `axiom_state_v1`), restaurer la dernière conversation ouverte au rechargement, et permettre la suppression via une corbeille dans l'historique.

**Architecture:** Nouveau module `frontend/lib/storage.ts` (lecture/écriture atomique d'un objet `AxiomState` versionné) + extraction des types partagés dans `frontend/lib/types.ts` + hydratation après montage et écriture par effet dans `frontend/app/page.tsx`. Les conversations de démo (s1/s2) sont supprimées — premier lancement = historique vide.

**Tech Stack:** Next.js 16.2.12 (Turbopack), React 19, TypeScript 5.7, Phosphor Icons.

## Global Constraints

(Copiées verbatim de la spec `docs/superpowers/specs/2026-08-02-conversation-persistence-design.md`)

- Clé localStorage unique versionnée : `axiom_state_v1`, objet `{ version: 1, sessions, tasks, activeSessionId }` — écriture atomique de l'objet entier.
- `loadState()` : clé absente, JSON invalide ou version inconnue → état vide (`sessions: []`, `tasks: []`, `activeSessionId: null`). Aucune exception propagée au composant.
- `saveState(state): boolean` : retourne `false` uniquement si l'écriture échoue alors que localStorage est disponible (ex. quota) ; si localStorage est indisponible → no-op silencieux qui retourne `true` (aucun toast).
- Au rechargement : rouvrir la dernière conversation active (`activeSessionId` trouvée dans `sessions`) avec son fil ; sinon première session ; sinon conversation vide.
- Corbeille : suppression directe SANS confirmation + toast « Conversation supprimée » ; si la conversation supprimée est celle ouverte → nouvelle conversation vide.
- `currentId` passe en `string | null` ; vérifié compatible avec tous ses usages (`s.id === currentId` l.396/653/292 de page.tsx).
- Hydratation après montage (pattern ThemeProvider) → aucun mismatch SSR/hydration ; pendant l'hydratation le chat affiche l'état vide.
- Les interfaces `Message` (avec `file?: string`), `ConversationSession`, `ScheduledTask`, `Toast` sont extraites dans `frontend/lib/types.ts` et importées par `page.tsx` (noms identiques).
- Démos s1/s2 retirées de l'état initial.
- Vérifications : `npx tsc --noEmit` puis `npm run lint` dans `frontend/` ; test manuel navigateur (aucun framework de test frontend).
- PAS de repo git dans `C:\Users\hp\Desktop\hakimagent` → les étapes « Commit » sont à SKIPPER.
- Outil Windows PowerShell : pas de `&&`/`||` — utiliser `;` et `if ($?) { ... }`.

---

### Task 1: Modules partagés — types.ts et storage.ts

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/storage.ts`
- Modify: `frontend/app/page.tsx:17-48` (suppression des interfaces locales au profit des imports)

**Interfaces:**
- Produces:
  - `interface Message { id: string; role: 'user' | 'assistant'; content: string; agent?: string; model?: string; score?: number; duration?: string; file?: string }` (exporté de `types.ts`)
  - `interface ConversationSession { id: string; title: string; subtitle: string; messages: Message[] }`
  - `interface ScheduledTask { id: string; name: string; schedule: string; status: 'active' | 'paused' }`
  - `interface Toast { id: string; type: 'success' | 'error' | 'info'; message: string }`
  - `interface AxiomState { version: 1; sessions: ConversationSession[]; tasks: ScheduledTask[]; activeSessionId: string | null }`
  - `isStorageAvailable(): boolean`
  - `loadState(): AxiomState`
  - `saveState(state: AxiomState): boolean`

- [ ] **Step 1: Créer `frontend/lib/types.ts`**

```ts
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agent?: string
  model?: string
  score?: number
  duration?: string
  file?: string
}

export interface ConversationSession {
  id: string
  title: string
  subtitle: string
  messages: Message[]
}

export interface ScheduledTask {
  id: string
  name: string
  schedule: string
  status: 'active' | 'paused'
}

export interface Toast {
  id: string
  type: 'success' | 'error' | 'info'
  message: string
}
```

- [ ] **Step 2: Créer `frontend/lib/storage.ts`**

```ts
import { ConversationSession, ScheduledTask } from './types'

export interface AxiomState {
  version: 1
  sessions: ConversationSession[]
  tasks: ScheduledTask[]
  activeSessionId: string | null
}

const STORAGE_KEY = 'axiom_state_v1'

const EMPTY_STATE: AxiomState = { version: 1, sessions: [], tasks: [], activeSessionId: null }

export function isStorageAvailable(): boolean {
  if (typeof window === 'undefined') return false
  try {
    window.localStorage.setItem('__axiom_test__', '1')
    window.localStorage.removeItem('__axiom_test__')
    return true
  } catch {
    return false
  }
}

export function loadState(): AxiomState {
  if (!isStorageAvailable()) return EMPTY_STATE
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return EMPTY_STATE
    const parsed: unknown = JSON.parse(raw)
    if (typeof parsed !== 'object' || parsed === null) return EMPTY_STATE
    const p = parsed as Record<string, unknown>
    if (p.version !== 1) return EMPTY_STATE
    return {
      version: 1,
      sessions: Array.isArray(p.sessions) ? (p.sessions as ConversationSession[]) : [],
      tasks: Array.isArray(p.tasks) ? (p.tasks as ScheduledTask[]) : [],
      activeSessionId: typeof p.activeSessionId === 'string' ? p.activeSessionId : null,
    }
  } catch {
    return EMPTY_STATE
  }
}

export function saveState(state: AxiomState): boolean {
  if (!isStorageAvailable()) return true
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    return true
  } catch {
    return false
  }
}
```

- [ ] **Step 3: Retirer les interfaces locales de `page.tsx`**

Supprimer le bloc `TYPES` de `frontend/app/page.tsx` (lignes 17-48, de `/* ================================================================` jusqu'à la fermeture `}` de l'interface `Toast` inclus), puis ajouter dans l'import existant (ligne 12) :

```tsx
import { getHealth, chat, HealthStatus } from '@/lib/api'
import { Message, ConversationSession, ScheduledTask, Toast } from '@/lib/types'
```

Ne pas supprimer le composant `ToastStack` ni aucun autre usage : les noms des types restent identiques, seul leur lieu de définition change.

- [ ] **Step 4: Vérifier la compilation TypeScript**

Run (dans `frontend/`) : `npx tsc --noEmit 2>&1`
Expected: aucune sortie (succès silencieux).

- [ ] **Step 5: Commit — SKIP (pas de repo git)**

---

### Task 2: Hydratation et écriture automatique dans page.tsx

**Files:**
- Modify: `frontend/app/page.tsx:218-222` (états initiaux), `frontend/app/page.tsx:232-235` (effets), ajout de l'import storage (ligne 12-15)

**Interfaces:**
- Consumes: `loadState`, `saveState` de `lib/storage.ts` (Task 1)
- Produces:
  - `hydrated: boolean` + `setHydrated` (état React)
  - Effet d'hydratation (une fois au montage, côté client uniquement)
  - Effet d'écriture automatique (sur `[sessions, tasks, currentId, hydrated]`)

- [ ] **Step 1: Ajouter l'import storage**

Dans `frontend/app/page.tsx`, après l'import des types (ligne 12-13), ajouter :

```tsx
import { loadState, saveState } from '@/lib/storage'
```

- [ ] **Step 2: Remplacer les états initiaux**

Remplacer (lignes 195-222) l'état `sessions` (dont les deux sessions de démonstration s1/s2, soit tout le bloc `useState<ConversationSession[]>([...])`), `currentId`, `messages` et `tasks` par :

```tsx
  const [sessions, setSessions] = useState<ConversationSession[]>([])
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [tasks, setTasks] = useState<ScheduledTask[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
```

Conserver ensuite tels quels les états « New task form » (`creatingTask`, `newTaskName`, `newTaskSched`), les refs `scrollRef`/`inputRef` et les deux `useEffect` de `getHealth`/scroll (lignes 229-235).

- [ ] **Step 3: Ajouter le flag et les deux effets**

Après l'effet de scroll (ligne 235), insérer :

```tsx
  const [hydrated, setHydrated] = useState(false)

  /* --- Hydratation depuis localStorage (après montage, pattern ThemeProvider) --- */
  useEffect(() => {
    const state = loadState()
    setSessions(state.sessions)
    setTasks(state.tasks)
    const active = state.sessions.find(s => s.id === state.activeSessionId)
    if (active) {
      setCurrentId(active.id)
      setMessages(active.messages)
    } else if (state.sessions.length > 0) {
      setCurrentId(state.sessions[0].id)
      setMessages(state.sessions[0].messages)
    }
    setHydrated(true)
  }, [])

  /* --- Écriture automatique (atomique, versionnée) --- */
  useEffect(() => {
    if (!hydrated) return
    const ok = saveState({ version: 1, sessions, tasks, activeSessionId: currentId })
    if (!ok) pushToast('error', 'Stockage local plein — conversation non enregistrée')
  }, [sessions, tasks, currentId, hydrated])
```

L'ordre de déclaration est important : l'effet d'hydratation DOIT être déclaré avant l'effet d'écriture (les effets s'exécutent dans l'ordre de déclaration), et le flag `hydrated` garantit qu'aucune écriture n'a lieu avant la restauration.

- [ ] **Step 4: Vérifier la compilation TypeScript**

Run (dans `frontend/`) : `npx tsc --noEmit 2>&1`
Expected: aucune sortie. Vérifier notamment que `s.id === currentId` (lignes 396, 653, 292) compile avec `currentId: string | null`.

- [ ] **Step 5: Commit — SKIP (pas de repo git)**

---

### Task 3: Corbeille de suppression dans l'Historique

**Files:**
- Modify: `frontend/app/page.tsx` — import Phosphor (lignes 5-11), handler `deleteSession` (près de `selectSession`, ligne 247-251), vue Historique (lignes 640-661)

**Interfaces:**
- Consumes: `sessions`, `setSessions`, `currentId`, `newConversation`, `pushToast` (Task 2)
- Produces:
  - `deleteSession(id: string): void`

- [ ] **Step 1: Ajouter l'icône Trash à l'import Phosphor**

Dans l'import `@phosphor-icons/react` (lignes 5-11), ajouter `Trash` (alphabetique) :

```tsx
  Lightning, TreeStructure, Robot, Sparkle, Trash, X
```

- [ ] **Step 2: Ajouter le handler deleteSession**

Après `selectSession` (ligne 247-251), insérer :

```tsx
  const deleteSession = (id: string) => {
    setSessions(p => p.filter(x => x.id !== id))
    if (id === currentId) newConversation()
    pushToast('success', 'Conversation supprimée')
  }
```

Note : `newConversation()` appelle `setSessions(p => [{ nouvelle session }, ...p])` — React compose les deux updaters dans l'ordre, la nouvelle session est donc ajoutée à la liste déjà filtrée.

- [ ] **Step 3: Remplacer la pastille/bouton DotsThree par corbeille + pastille**

Dans la vue Historique (lignes 653-658), remplacer :

```tsx
                    {s.id === currentId
                      ? <div className="w-2.5 h-2.5 rounded-full bg-cyan-400" style={{ boxShadow: '0 0 8px rgba(6,182,212,.8)' }} />
                      : <button className="input-action-btn" onClick={e => e.stopPropagation()}>
                          <DotsThree className="w-5 h-5" weight="bold" />
                        </button>
                    }
```

par :

```tsx
                    <div className="flex items-center gap-1.5">
                      {s.id === currentId && (
                        <div className="w-2.5 h-2.5 rounded-full bg-cyan-400" style={{ boxShadow: '0 0 8px rgba(6,182,212,.8)' }} />
                      )}
                      <button
                        className="input-action-btn"
                        onClick={e => e.stopPropagation()}
                        title="Supprimer la conversation"
                        aria-label="Supprimer la conversation"
                      >
                        <Trash className="w-4 h-4" />
                      </button>
                    </div>
```

Le `stopPropagation` empêche le clic corbeille de déclencher `selectSession` sur la ligne (`motion.div` onClick).

- [ ] **Step 4: Vérifier TypeScript et lint**

Run (dans `frontend/`) :
```
npx tsc --noEmit 2>&1
```
Expected: aucune sortie.

Run :
```
npm run lint 2>&1
```
Expected: pas d'erreur ESLint.

- [ ] **Step 5: Commit — SKIP (pas de repo git)**

---

### Task 4: Test manuel navigateur

**Files:**
- Aucun fichier — vérification fonctionnelle sur http://localhost:3000

- [ ] **Step 1: Démarrer le serveur frontend**

Run (dans `frontend/`) — si pas déjà lancé :
```
npm run dev
```
Ouvrir http://localhost:3000. Afficher la console du navigateur (F12) pour contrôler les erreurs éventuelles.

- [ ] **Step 2: Tester le scénario complet**

1. **Premier lancement** : localStorage vide → historique vide, aucune démo s1/s2, chat vide (« Comment puis-je vous aider ? »).
2. Envoyer un message (le backend peut être down → un message d'erreur « Erreur de connexion au backend AXIOM » s'affiche, c'est acceptable) → le message utilisateur apparaît.
3. Recharger la page (F5) → la conversation est rouverte avec son fil (et le message d'erreur éventuel).
4. Créer une conversation (sidebar « Nouvelle conversation ») → envoyer un message → recharger → les DEUX conversations sont dans la sidebar et l'Historique ; la dernière ouverte est rouverte.
5. Créer une tâche (onglet Tâches → Nouvelle → Créer) → recharger → la tâche est toujours listée.
6. Vérifier dans DevTools (Application → Local Storage → http://localhost:3000) : clé `axiom_state_v1` contenant `version: 1` avec `sessions`, `tasks`, `activeSessionId`.

- [ ] **Step 3: Tester la corbeille**

1. Onglet Historique → cliquer la corbeille d'une conversation non active → disparaît + toast « Conversation supprimée ».
2. Supprimer la conversation active → bascule sur une nouvelle conversation vide.
3. Recharger → les conversations supprimées restent absentes (persistance de la suppression).

- [ ] **Step 4: Commit — SKIP (pas de repo git)**

---

## Self-Review

- **Couverture spec** : état vide au premier lancement / démos retirées (✓ Task 2 Step 2), rouvrir la dernière active (✓ Task 2 Step 3), écriture automatique atomique (✓ Task 2 Step 3), corbeille sans confirmation + toast + bascule (✓ Task 3), quota → toast (✓ Task 2 Step 3, `saveState` false), localStorage indisponible → no-op silencieux (✓ Task 1 Step 2, `saveState` true), JSON corrompu/version inconnue → état vide (✓ Task 1 Step 2), `currentId: string | null` vérifié (✓ Task 2 Step 4), tests manuels 5 cas (✓ Task 4).
- **Placeholders** : aucun — code complet dans chaque étape.
- **Cohérence des types** : `Message`/`ConversationSession`/`ScheduledTask`/`Toast` exportés de `types.ts` et importés par `page.tsx` (noms identiques) ; `AxiomState`/`loadState`/`saveState`/`isStorageAvailable` définis Task 1, consommés Task 2 avec les mêmes signatures. Le champ `Message.file` est déjà inclus pour la future fonctionnalité trombone (le plan trombone `2026-08-02-file-attachment.md` devra retirer son étape « étendre l'interface Message » — déjà dans `types.ts`).
