# Attachement de fichier (trombone) — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rendre fonctionnel le bouton trombone (📎) de la barre de saisie de la page d'accueil : joindre un fichier texte/code dont le contenu est injecté comme contexte dans le message envoyé à `/chat`.

**Architecture:** Lecture du fichier côté client (`FileReader.readAsText`), construction d'un message enrichi (`Fichier joint "nom" : <bloc code> — Question : <texte>`), envoi via l'endpoint `/chat` existant. Aucun changement backend. Toute la logique vit dans `frontend/app/page.tsx`.

**Tech Stack:** Next.js 16.2.12 (Turbopack), React 19, TypeScript 5.7, Phosphor Icons, framer-motion.

## Global Constraints

- Aucun changement dans le backend ni dans `lib/api.ts` (approche validée).
- Langue de l'UI : français (toasts, badges) — cohérent avec `page.tsx` existant.
- Taille max fichier : 100 Ko. Extensions acceptées : `.txt`, `.md`, `.markdown`, `.py`, `.js`, `.mjs`, `.ts`, `.tsx`, `.jsx`, `.json`, `.csv`, `.html`, `.css`, `.scss`, `.sql`, `.yaml`, `.yml`, `.xml`, `.sh`, `.bat`, `.cmd`, `.ps1`, `.ini`, `.cfg`, `.toml`, `.env`, `.log`.
- Un seul fichier joint à la fois (le nouveau remplace l'ancien).
- Le trombone est désactivé pendant `loading`.
- PAS de repo git dans `C:\Users\hp\Desktop\hakimagent` → les étapes « Commit » sont à SKIPPER (noté explicitement à chaque fois).
- Vérifications : `npx tsc --noEmit` et `npm run lint` dans `frontend/`. Pas de framework de test frontend → test manuel navigateur.
- Outil Windows PowerShell : pas de `&&`/`||` — utiliser `;` et `if ($?) { ... }`.

---

### Task 1: Constantes et état d'attachement

**Files:**
- Modify: `frontend/app/page.tsx` — import X (déjà présent, ligne 10), constante `Message` (ligne 20-28), état du composant `Home` (après ligne 221), handlers (près de `handleSend`, ligne 267)

**Interfaces:**
- Produces:
  - `const ACCEPTED_EXTENSIONS: string[]` — liste des extensions acceptées (sans point, minuscules)
  - `const MAX_FILE_SIZE = 100 * 1024` (octets)
  - `const EXT_TO_LANG: Record<string, string>` — map extension→langage (sans point)
  - `attachedFile: File | null` + `setAttachedFile` (état React)
  - `fileInputRef: React.RefObject<HTMLInputElement | null>` (useRef)
  - `handleAttachClick(): void` — déclenche `fileInputRef.current?.click()`
  - `handleFileSelected(e: React.ChangeEvent<HTMLInputElement>): void` — valide (extension, taille, vide) puis `setAttachedFile(file)`
  - `readFileContent(file: File): Promise<string>` — `FileReader.readAsText` UTF-8, rejette en cas d'erreur

- [ ] **Step 1: Ajouter les constantes d'extensions et langages**

Après le bloc `const SUGGESTIONS = [...]` (ligne 70-75) de `frontend/app/page.tsx`, insérer :

```tsx
const ACCEPTED_EXTENSIONS = [
  'txt', 'md', 'markdown', 'py', 'js', 'mjs', 'ts', 'tsx', 'jsx',
  'json', 'csv', 'html', 'css', 'scss', 'sql', 'yaml', 'yml', 'xml',
  'sh', 'bat', 'cmd', 'ps1', 'ini', 'cfg', 'toml', 'env', 'log',
]

const MAX_FILE_SIZE = 100 * 1024

const EXT_TO_LANG: Record<string, string> = {
  py: 'python', js: 'javascript', mjs: 'javascript', ts: 'typescript',
  tsx: 'typescript', jsx: 'javascript', json: 'json', md: 'markdown',
  markdown: 'markdown', html: 'html', css: 'css', scss: 'scss',
  sql: 'sql', yml: 'yaml', yaml: 'yaml', xml: 'xml', sh: 'bash',
  bat: 'batch', cmd: 'batch', ps1: 'powershell', ini: 'ini',
  cfg: 'ini', toml: 'toml', env: 'bash', log: 'text', txt: 'text',
  csv: 'csv',
}
```

- [ ] **Step 2: Ajouter l'état et les handlers d'attachement**

Dans le composant `Home()`, après `const [newTaskSched, setNewTaskSched] = useState('')` (ligne 227), ajouter :

```tsx
const [attachedFile, setAttachedFile] = useState<File | null>(null)
const fileInputRef = useRef<HTMLInputElement>(null)
```

Après le handler `useSuggestion` (ligne 253-256), ajouter :

```tsx
const handleAttachClick = () => fileInputRef.current?.click()

const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  if (!ACCEPTED_EXTENSIONS.includes(ext)) {
    pushToast('error', 'Type de fichier non supporté')
    return
  }
  if (file.size === 0) {
    pushToast('error', 'Fichier vide')
    return
  }
  if (file.size > MAX_FILE_SIZE) {
    pushToast('error', 'Fichier trop volumineux (max 100 Ko)')
    return
  }
  setAttachedFile(file)
  pushToast('success', `Fichier joint : ${file.name}`)
}

const readFileContent = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('read-failed'))
    reader.readAsText(file, 'utf-8')
  })
```

- [ ] **Step 3: Vérifier la compilation TypeScript**

Run (dans `frontend/`) : `npx tsc --noEmit 2>&1`
Expected: aucune sortie (succès silencieux). Le champ `useRef` et les types doivent compiler sans erreur (React 19 : `useRef<HTMLInputElement>(null)` est valide).

- [ ] **Step 4: Commit — SKIP (pas de repo git)**

---

### Task 2: Intégration UI — input caché, chip, badge et envoi

**Files:**
- Modify: `frontend/app/page.tsx` — interface `Message` (ligne 20-28), `handleSend` (ligne 267-303), rendu des messages utilisateur (ligne 493-503), bouton trombone (ligne 573-579), zone au-dessus de la barre de saisie (ligne 551-552)

**Interfaces:**
- Consumes: `attachedFile`, `setAttachedFile`, `fileInputRef`, `handleAttachClick`, `handleFileSelected`, `readFileContent`, `MAX_FILE_SIZE`, `EXT_TO_LANG` (Task 1)
- Produces:
  - Champ `file?: string` sur l'interface `Message` (nom du fichier joint pour l'affichage du badge)
  - `handleSend` : lit le fichier si présent, construit le message enrichi, envoie `chat(finalContent)`, réinitialise `attachedFile`
  - Chip `📎 <nom> <taille> ✕` au-dessus de la barre de saisie quand `attachedFile != null`
  - Badge `📎 <nom>` sous le message utilisateur quand `msg.file` existe
  - `<input type="file">` masqué avec `accept` = extensions, `onChange` = `handleFileSelected`

- [ ] **Step 1: Étendre l'interface Message — DÉJÀ COUVERT**

Le plan de persistance (`2026-08-02-conversation-persistence.md`) a extrait les interfaces dans `frontend/lib/types.ts`, avec `file?: string` DÉJÀ inclus sur `Message` (ligne 7 de `types.ts`). Aucune modification nécessaire ici — le badge utilisera `msg.file` directement. Vérifier uniquement que `frontend/lib/types.ts` contient bien `file?: string` avant de continuer.

- [ ] **Step 2: Modifier handleSend pour injecter le fichier**

Dans `handleSend` (ligne 267-303), remplacer le bloc allant de `const t0 = Date.now()` jusqu'à `setMessages(next)` par :

```tsx
    const t0 = Date.now()
    let finalContent = text
    let fileName: string | undefined
    if (attachedFile) {
      try {
        const content = await readFileContent(attachedFile)
        const ext = (attachedFile.name.split('.').pop() || '').toLowerCase()
        const lang = EXT_TO_LANG[ext] || ''
        const sizeKo = (attachedFile.size / 1024).toFixed(1)
        fileName = attachedFile.name
        finalContent =
          `Fichier joint "${attachedFile.name}" (${sizeKo} Ko) :\n` +
          '```' + lang + '\n' + content + '\n```\n\n' +
          `Question : ${text}`
      } catch {
        pushToast('error', 'Impossible de lire le fichier')
        return
      }
    }
    const um: Message = { id: 'u-' + t0, role: 'user', content: text, file: fileName }
    const next = [...messages, um]
    setMessages(next)
    setLoading(true)
```

puis, dans le `finally` (ligne 300-302), ajouter la réinitialisation de la chip :

```tsx
    } finally {
      setLoading(false)
      setAttachedFile(null)
    }
```

- [ ] **Step 3: Badge fichier sous les messages utilisateur**

Remplacer le bloc de rendu utilisateur (ligne 493-503) :

```tsx
                    if (msg.role === 'user') return (
                      <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ type: 'spring', stiffness: 260, damping: 26 }}
                        className="flex justify-end"
                      >
                        <div className="msg-user">{msg.content}</div>
                      </motion.div>
                    )
```

par :

```tsx
                    if (msg.role === 'user') return (
                      <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ type: 'spring', stiffness: 260, damping: 26 }}
                        className="flex justify-end"
                      >
                        <div className="flex flex-col items-end gap-1.5 max-w-[85%]">
                          <div className="msg-user">{msg.content}</div>
                          {msg.file && (
                            <div
                              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono"
                              style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
                            >
                              <span>📎</span>
                              <span className="truncate max-w-[240px]">{msg.file}</span>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )
```

- [ ] **Step 4: Remplacer le handler du trombone + input caché + chip**

Remplacer le bouton trombone (ligne 573-579) :

```tsx
                    <button
                      className="input-action-btn"
                      title="Joindre un fichier"
                      onClick={() => pushToast('info', 'Fonctionnalité de fichier bientôt disponible')}
                    >
                      <Paperclip className="w-4 h-4" />
                    </button>
```

par :

```tsx
                    <button
                      className="input-action-btn"
                      title="Joindre un fichier"
                      aria-label="Joindre un fichier"
                      onClick={handleAttachClick}
                      disabled={loading}
                    >
                      <Paperclip className="w-4 h-4" />
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept={ACCEPTED_EXTENSIONS.map(e => '.' + e).join(',')}
                      onChange={handleFileSelected}
                      className="hidden"
                      tabIndex={-1}
                      aria-hidden="true"
                    />
```

Puis, entre la fin de la zone messages (fermeture `</div>` du scroll, ligne 549) et le bloc input (ligne 552), insérer la chip :

```tsx
            {/* Attached file chip */}
            {attachedFile && (
              <div className="max-w-2xl mx-auto w-full px-4 pt-2">
                <div
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl"
                  style={{ background: 'var(--bg-tertiary)', border: '1.5px solid var(--border)' }}
                >
                  <span>📎</span>
                  <span className="text-xs font-mono flex-1 truncate" style={{ color: 'var(--text-primary)' }}>
                    {attachedFile.name}
                  </span>
                  <span className="text-xs font-mono shrink-0" style={{ color: 'var(--text-muted)' }}>
                    {(attachedFile.size / 1024).toFixed(1)} Ko
                  </span>
                  <button
                    onClick={() => setAttachedFile(null)}
                    className="input-action-btn shrink-0"
                    title="Retirer le fichier"
                    aria-label="Retirer le fichier"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
```

Note : le bouton trombone est dans la vue « chat » uniquement ; la chip est insérée au même endroit (le bloc est conditionné par `view === 'chat'`, donc insérer la chip dans ce même bloc, juste après la div scroll `ref={scrollRef}`).

- [ ] **Step 5: Vérifier TypeScript et lint**

Run (dans `frontend/`) :
```
npx tsc --noEmit 2>&1
```
Expected: aucune sortie.

Run :
```
npm run lint 2>&1
```
Expected: "✔ No ESLint warnings or errors" (ou message équivalent, sans erreur).

- [ ] **Step 6: Commit — SKIP (pas de repo git)**

---

### Task 3: Test manuel navigateur

**Files:**
- Aucun fichier — vérification fonctionnelle sur http://localhost:3000

- [ ] **Step 1: Démarrer les serveurs**

Backend (dans `backend/`) :
```
python -m uvicorn axiom.api.main:app --host 0.0.0.0 --port 8000
```
Frontend (dans `frontend/`) — si pas déjà lancé :
```
npm run dev
```
Ouvrir http://localhost:3000 dans le navigateur.

- [ ] **Step 2: Tester le scénario nominal**

1. Cliquer sur le trombone → le sélecteur de fichiers s'ouvre, filtré sur les extensions acceptées.
2. Sélectionner un fichier `.py` (ex. un fichier existant du projet, taille < 100 Ko) → une chip `📎 <nom> <taille> Ko` apparaît au-dessus de la barre de saisie + toast « Fichier joint : <nom> ».
3. Saisir « Analyse ce fichier » et envoyer → le message utilisateur s'affiche avec un badge `📎 <nom>` en dessous ; la chip disparaît ; le backend reçoit le contenu du fichier comme contexte (réponse de l'agent incluant le contenu, si clé OpenRouter configurée ; sinon toast d'erreur de connexion — acceptable, le backend n'est pas configuré).
4. Vérifier que le message affiché dans le chat ne contient que le texte utilisateur (pas le contenu du fichier).

- [ ] **Step 3: Tester les cas limites**

1. Retirer la chip avec ✕ avant envoi → envoyer → aucun badge sur le message.
2. Joindre un fichier, puis un second → la chip affiche le second fichier (remplacement).
3. Pendant `loading` (réponse en cours), le trombone est désactivé (grisé).
4. Fichier > 100 Ko → toast « Fichier trop volumineux (max 100 Ko) », pas de chip.
5. Fichier `.zip` ou `.exe` → toast « Type de fichier non supporté », pas de chip.
6. Fichier vide (0 octet) → toast « Fichier vide », pas de chip.

- [ ] **Step 4: Commit — SKIP (pas de repo git)**

---

## Self-Review

- **Couverture spec** : chip (✓ Task 2 Step 4), injection du contexte (✓ Task 2 Step 2), badge (✓ Task 2 Step 3), limites/erreurs (✓ Task 1 Step 2), remplacement fichier (✓ `setAttachedFile` remplace, Task 1), désactivation pendant loading (✓ `disabled={loading}` Task 2 Step 4), tests tsc/lint (✓ Task 2 Step 5), test manuel (✓ Task 3).
- **Placeholders** : aucun — tout le code réel est fourni dans chaque étape.
- **Cohérence des types** : `attachedFile: File | null`, `handleFileSelected`, `readFileContent(file: File): Promise<string>`, `Message.file?: string` — cohérents entre les tasks. `EXT_TO_LANG` et `ACCEPTED_EXTENSIONS` sont définis dans Task 1 et utilisés dans Task 1/2 avec les mêmes noms.
