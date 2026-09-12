# Control Room Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refondre l'interface HakimAgent en une console de pilotage sombre, cohérente, responsive et accessible, sans modifier ses contrats backend.

**Architecture:** Les jetons CSS et primitives visuelles partagées constituent la base. Un shell applicatif réutilisable unifie navigation et en-têtes, puis les pages produit emploient ces primitives sans modifier leurs appels à `lib/api.ts` ni le contexte d'authentification. Les animations Framer Motion existantes restent limitées aux entrées et interactions utiles.

**Tech Stack:** Next.js 16, React 19, TypeScript 5.7, Tailwind CSS 4, Framer Motion, Phosphor Icons.

**Spec:** `docs/superpowers/specs/2026-09-02-control-room-redesign.md`

## Global Constraints

- Frontend uniquement : ne pas modifier `backend/`, les routes API, l'authentification ou les contrats TypeScript existants.
- Ne pas ajouter de dépendance.
- Thème sombre bleu-noir par défaut et thème clair aligné sur les mêmes jetons sémantiques.
- Respecter WCAG AA : texte normal à contraste de 4,5:1 minimum, focus visible, boutons iconiques étiquetés.
- Les routes `/`, `/agents`, `/chat`, `/memory`, `/tools` et `/login` doivent rester fonctionnelles.
- Vérifier les mises en page à 360 px, 768 px, 1024 px et 1440 px, sans défilement horizontal.
- Le dossier ne contient pas de dépôt Git : toute étape de commit est explicitement ignorée.

---

## File structure

- Create: `frontend/components/AppShell.tsx` — shell responsive, barre supérieure et navigation mobile.
- Create: `frontend/components/PageHeader.tsx` — en-tête de page homogène.
- Create: `frontend/components/ui-kit.tsx` — primitives `Panel`, `StatusBadge` et `EmptyState`.
- Modify: `frontend/app/globals.css` — jetons, styles fondation et utilitaires partagés.
- Modify: `frontend/components/Sidebar.tsx` — navigation de bureau accessible et alignée au shell.
- Modify: `frontend/components/GlassCard.tsx` — faire pointer les cartes métriques vers les jetons sans effet décoratif permanent.
- Modify: `frontend/app/page.tsx` — page d'accueil de pilotage.
- Modify: `frontend/app/agents/page.tsx`, `frontend/app/memory/page.tsx`, `frontend/app/tools/page.tsx` — pages opérationnelles homogènes.
- Modify: `frontend/app/chat/page.tsx`, `frontend/components/ChatPanel.tsx` — conversation et compositeur cohérents.
- Modify: `frontend/app/login/page.tsx` — connexion accessible et cohérente.

## Task 1: Jetons et fondations d'interface

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/components/ThemeProvider.tsx`

**Interfaces:**
- Consumes: classes et variables CSS déjà utilisées (`--bg`, `--surface`, `--accent`, `.page-title`, `.input-axiom`, `.btn-primary`).
- Produces: jetons supplémentaires `--surface-raised`, `--success`, `--warning`, `--danger`, `--focus-ring`, ainsi que des styles communs de focus et de surface.

- [ ] **Step 1: Définir les jetons dans les deux thèmes.**

Ajouter dans `:root`, puis redéfinir les mêmes noms dans le sélecteur sombre :

```css
--surface-raised: #1c2740;
--success: #43d19e;
--warning: #f8bf5a;
--danger: #f57678;
--focus-ring: #68d9ff;
```

Utiliser un fond sombre bleu-noir (`--bg`) et un accent cyan; conserver les mêmes noms de variables actuellement consommés par les composants.

- [ ] **Step 2: Ajouter des fondations accessibles.**

Ajouter les règles suivantes après les styles de base :

```css
:where(button, a, input, textarea, select):focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 3px;
}

.control-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow-sm);
}
```

Veiller à ce que les styles de bouton et champ existants utilisent `--surface-raised`, `--border` et les couleurs d'état plutôt que des hexadécimaux répétés.

- [ ] **Step 3: Conserver le thème sombre par défaut sans clignotement.**

Dans `ThemeProvider.tsx`, conserver la clé `axiom_theme` et la valeur par défaut `true`. Ajouter l'attribut `data-theme` à `document.documentElement` avant le rendu des enfants lorsqu'une préférence existe, sans écrire de token dans `localStorage` hors de `applyTheme`.

- [ ] **Step 4: Vérifier les types et le build de base.**

Run: `npx tsc --noEmit; npm run build` depuis `frontend/`.

Expected: deux commandes terminent avec le code 0.

- [ ] **Step 5: Commit.**

Skip : aucun dépôt Git dans le projet.

## Task 2: Shell, navigation et primitives partagées

**Files:**
- Create: `frontend/components/AppShell.tsx`
- Create: `frontend/components/PageHeader.tsx`
- Create: `frontend/components/ui-kit.tsx`
- Modify: `frontend/components/Sidebar.tsx`

**Interfaces:**
- `AppShell({ children }: { children: React.ReactNode })` enveloppe chaque page connectée.
- `PageHeader({ eyebrow, title, description, actions })` rend l'en-tête commun.
- `Panel`, `StatusBadge` et `EmptyState` acceptent `children` et un `className` optionnel; aucun appel API.

- [ ] **Step 1: Créer les primitives sans état.**

Créer `ui-kit.tsx` avec des composants sémantiques :

```tsx
export function Panel({ children, className = '' }: React.PropsWithChildren<{ className?: string }>) {
  return <section className={`control-panel ${className}`}>{children}</section>
}

export function StatusBadge({ tone, children }: React.PropsWithChildren<{ tone: 'success' | 'warning' | 'danger' | 'neutral' }>) {
  return <span className={`status-badge status-badge--${tone}`}>{children}</span>
}
```

`EmptyState` accepte `title`, `description` et `action?: React.ReactNode`, et rend une section centrée sans illustration emoji.

- [ ] **Step 2: Créer `PageHeader`.**

Le composant rend `eyebrow`, un unique `h1`, `description` optionnelle et une zone `actions` qui passe sous le titre en dessous de `md` :

```tsx
type PageHeaderProps = { eyebrow?: string; title: string; description?: string; actions?: React.ReactNode }
```

- [ ] **Step 3: Créer le shell responsive.**

`AppShell` affiche `Sidebar` à partir de `lg`, un bouton menu avec `aria-expanded` et `aria-controls` en dessous de `lg`, puis une barre supérieure. Le menu mobile se ferme au clic d'un lien et avec `Escape`. Son panneau porte `role="dialog"` et `aria-label="Navigation principale"`.

- [ ] **Step 4: Adapter `Sidebar.tsx`.**

Garder le tableau `NAV`, les routes et le sélecteur de thème. Remplacer les valeurs de largeur et bordure en ligne par les classes du shell, ajouter `aria-current="page"` au lien actif et rendre le statut API via `StatusBadge`.

- [ ] **Step 5: Vérifier le shell.**

Run: `npx tsc --noEmit` depuis `frontend/`.

Expected: code 0; le menu mobile et la barre latérale ne nécessitent aucun nouveau package.

- [ ] **Step 6: Commit.**

Skip : aucun dépôt Git dans le projet.

## Task 3: Accueil et écrans de pilotage

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/agents/page.tsx`
- Modify: `frontend/app/memory/page.tsx`
- Modify: `frontend/app/tools/page.tsx`
- Modify: `frontend/components/AgentCard.tsx`
- Modify: `frontend/components/GlassCard.tsx`

**Interfaces:**
- Consumes: `getAgents`, `getMemory`, `webSearch`, `executeCode`, `createFile`, `getErrors` et `logError` sans changement de signature.
- Produces: mêmes actions utilisateur et contenus API, présentés avec `AppShell`, `PageHeader`, `Panel` et `EmptyState`.

- [ ] **Step 1: Recomposer l'accueil.**

Dans `app/page.tsx`, remplacer la navigation marketing et les sections décoratives par : un `PageHeader` (« Poste de commande »), quatre `MetricCard` déjà exportées, une zone « Démarrer une tâche » qui lie vers `/chat`, et un panneau synthèse des capacités. Ne changer ni `productName`, ni les données `metricCards`, ni les liens de navigation existants.

- [ ] **Step 2: Migrer Agents et Mémoire vers les primitives.**

Encapsuler leur contenu dans `AppShell`, utiliser `PageHeader`, puis remplacer les occurrences de `agent-card` pour les panneaux non-agent par `Panel`. Conserver l'affichage squelette lorsque `agents` ou `memory` est null. Pour les trois niveaux mémoire, utiliser un `aria-label` descriptif sur chaque bloc `pre`.

- [ ] **Step 3: Donner aux cartes agents une structure de statut.**

Dans `AgentCard.tsx`, conserver les props actuelles et rendre le statut via `StatusBadge`. Le nom est un `h2`, les capacités une liste sémantique, les métriques une liste `dl` ou une zone mono. Aucune donnée inventée ne doit être affichée.

- [ ] **Step 4: Transformer Outils en surface opérationnelle.**

Conserver les quatre actions et états React actuels. Utiliser `PageHeader`, puis quatre `Panel` avec `aria-labelledby` relié au `h2` du panneau. Tout résultat de recherche ou exécution reste dans un `pre` avec `tabIndex={0}` et `aria-label="Résultat ..."` afin d'être inspectable au clavier.

- [ ] **Step 5: Retirer les effets décoratifs des cartes partagées.**

Dans `GlassCard.tsx`, conserver l'API exportée. Remplacer le déplacement vertical automatique du `whileHover` par une bordure/ombre pilotée par CSS et respecter `prefers-reduced-motion` via `useReducedMotion()`.

- [ ] **Step 6: Vérifier les écrans de pilotage.**

Run: `npx tsc --noEmit; npm run build` depuis `frontend/`.

Expected: code 0. Ouvrir ensuite `/`, `/agents`, `/memory`, `/tools` à 360, 768, 1024 et 1440 px; aucun défilement horizontal et chaque action reste visible.

- [ ] **Step 7: Commit.**

Skip : aucun dépôt Git dans le projet.

## Task 4: Conversation et espace agent

**Files:**
- Modify: `frontend/app/chat/page.tsx`
- Modify: `frontend/components/ChatPanel.tsx`
- Modify: `frontend/app/agent/page.tsx`

**Interfaces:**
- Consumes: `useAuth`, `chat`, `executeTask`, `scoreTask`, pièces jointes et permissions existantes.
- Produces: mêmes requêtes réseau et états de chargement; seul le rendu évolue.

- [ ] **Step 1: Mettre le chat dans le shell.**

Dans `app/chat/page.tsx`, remplacer l'en-tête local et le couple `Sidebar`/`main` par `AppShell` et `PageHeader`. Préserver exactement `handleFileSelected`, `handleSend`, le format `finalContent`, le header `Authorization`, `credentials: 'include'` et la limite de 100 Ko.

- [ ] **Step 2: Clarifier la conversation.**

Rendre les messages utilisateur, assistant et système avec `data-role`. L'assistant affiche un statut et les métadonnées de tâche dans un `Panel` secondaire. L'état vide comprend une action qui place un exemple dans `input`, comme aujourd'hui; ne pas dupliquer un appel API.

- [ ] **Step 3: Ancrer le compositeur sans masquer les messages.**

Le conteneur de saisie utilise `sticky bottom-0` dans la colonne de conversation, `background: var(--surface-raised)` et un padding inférieur suffisant pour le contenu scrollable. Le bouton pièce jointe garde son `aria-label`; ajouter `aria-label="Envoyer le message"` au bouton d'envoi.

- [ ] **Step 4: Harmoniser `ChatPanel`.**

Garder son API et sa simulation de permission. Remplacer ses styles en ligne par les jetons et `Panel`; les boutons de modèle doivent devenir de vrais boutons (`type="button"`) ou une valeur non interactive, sans faux élément cliquable.

- [ ] **Step 5: Appliquer uniquement le chrome commun à `/agent`.**

Le fichier est volumineux : conserver ses sections, sa logique d'exécution et ses états. Remplacer seulement le conteneur extérieur et l'en-tête par `AppShell`/`PageHeader`, puis vérifier qu'aucun handler de permission ou `localStorage` n'est modifié.

- [ ] **Step 6: Vérifier les flux fonctionnels.**

Run: `npx tsc --noEmit; npm run build` depuis `frontend/`.

Expected: code 0. Test manuel : connexion, message, pièce jointe `.txt` sous 100 Ko, message de chargement et affichage de permission.

- [ ] **Step 7: Commit.**

Skip : aucun dépôt Git dans le projet.

## Task 5: Connexion, contrôle d'accessibilité et validation finale

**Files:**
- Modify: `frontend/app/login/page.tsx`
- Modify: `frontend/app/globals.css`

**Interfaces:**
- Consumes: `useAuth().login`, `useAuth().register` et redirection vers `/chat`.
- Produces: même soumission de formulaire avec une hiérarchie et erreurs accessibles.

- [ ] **Step 1: Recomposer la page de connexion.**

Conserver les états `isLogin`, `username`, `password`, `displayName`, `error` et `loading`. Utiliser un `main` avec `aria-labelledby="login-title"`, un logo APEX, un panneau `control-panel`, des labels reliés par `htmlFor` et des `id` explicites. L'erreur devient :

```tsx
{error && <p role="alert" className="form-error">{error}</p>}
```

Le bouton conserve `type="submit"`, `disabled={loading}` et les libellés actuels.

- [ ] **Step 2: Ajouter les styles réduisant le mouvement.**

Dans `globals.css`, ajouter :

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 3: Réaliser la vérification statique finale.**

Run: `npx tsc --noEmit; npm run build` depuis `frontend/`.

Expected: code 0 et export Next généré sans erreur.

- [ ] **Step 4: Réaliser la vérification manuelle finale.**

Lancer `npm run dev`, puis vérifier `/`, `/agents`, `/chat`, `/memory`, `/tools`, `/login` à 360, 768, 1024 et 1440 px. Au clavier, vérifier le skip link, le focus, l'ouverture/fermeture du menu mobile avec `Escape`, le changement de thème et la soumission de connexion. Ne conserver aucun serveur de test démarré après la vérification.

- [ ] **Step 5: Commit.**

Skip : aucun dépôt Git dans le projet.

## Self-review

- Couverture de la spécification : les tâches 1 et 2 couvrent jetons, shell, responsive et accessibilité; les tâches 3 et 4 couvrent tous les écrans produit; la tâche 5 couvre la connexion et la validation complète.
- Exhaustivité : chaque étape indique une action concrète, les fichiers concernés et son contrôle associé.
- Contrats : `AppShell`, `PageHeader`, `Panel`, `StatusBadge` et `EmptyState` sont définis avant leur consommation; aucune signature API n'est modifiée.
