# Spécification — Refonte « Control Room » de HakimAgent

**Date :** 2026-09-02  
**Statut :** Direction visuelle approuvée — en attente de revue de cette spécification  
**Périmètre :** frontend Next.js uniquement

## Objectif

Faire évoluer HakimAgent vers une interface de pilotage d'agents IA plus lisible, plus cohérente et plus crédible pour un usage quotidien. La direction retenue est un « control room » sombre : fonds bleu nuit nuancés, accent cyan/indigo, forte hiérarchie des informations et surfaces sobres. Les flux actuels (connexion, chat, exécution, mémoire, agents et outils) restent inchangés.

## Principes de conception

- **Clarté opérationnelle :** l'état du système, les actions principales et les résultats restent visibles sans surcharger la page.
- **Une seule grammaire visuelle :** mêmes espacements, bordures, boutons, badges, cartes et états vides sur toutes les pages produit.
- **Profondeur maîtrisée :** surfaces superposées, bordures discrètes et halos limités; aucun effet décoratif qui diminue le contraste.
- **Priorité au contenu :** typographie sans sérif pour l'interface, police mono réservée aux métriques, identifiants et sorties techniques.
- **Thème fiable :** thème sombre par défaut; thème clair conservé et aligné sur les mêmes jetons sémantiques.

## Architecture visuelle

### Jetons

`app/globals.css` devient la source de vérité pour les couleurs et mesures sémantiques : `--bg`, `--surface`, `--surface-raised`, `--border`, `--text-primary`, `--text-secondary`, `--text-muted`, `--accent`, `--success`, `--warning`, `--danger`, rayons, ombres et durées. Les composants n'emploient pas de couleurs métier codées en dur hors des jetons d'état.

Le thème sombre utilisera un bleu-noir profond avec des surfaces ardoise et un cyan électrique réservé aux interactions et données actives. Le contraste texte/fond doit satisfaire WCAG AA (4,5:1 pour le texte normal).

### Shell applicatif

Le shell comprend :

1. une barre latérale de bureau compacte avec logo, navigation, statut de connexion et réglages;
2. une barre supérieure contextuelle avec titre de page, fil d'Ariane optionnel, état système et commandes globales;
3. une zone de contenu limitée en largeur pour les pages éditoriales, mais fluide pour le chat et les tableaux de pilotage;
4. sur mobile, un en-tête compact et un panneau de navigation accessible au clavier, sans colonne fixe.

### Composants communs

- `AppShell` : structure, responsive et navigation mobile.
- `PageHeader` : libellé, titre, description courte, actions.
- `StatusBadge` : idle, actif, attente de permission, erreur et connecté.
- `MetricCard` : mesure, libellé, variation ou description et état.
- `Panel` : surface standardisée pour cartes, listes et modules.
- `EmptyState` : état d'absence avec explication et action suivante.

Les primitives actuelles sont réutilisées ou simplifiées; aucune bibliothèque supplémentaire n'est requise.

## Écrans concernés

| Écran | Refonte attendue |
| --- | --- |
| Accueil | Vue d'ensemble : état du système, capacités, flux de démarrage et métriques plutôt qu'une landing page hétérogène. |
| Agents | Grille de cartes lisible, capacités et états d'exécution immédiatement comparables. |
| Chat | Zone de conversation centrale, en-tête de session, messages distincts, compositeur ancré et panneau de contexte sur grand écran. |
| Mémoire | Résumé des trois couches de mémoire, jauges sobres et listes inspectables. |
| Outils | Catalogue en grille ou table, catégories, disponibilité et actions explicites. |
| Connexion | Formulaire centré, sécurisé visuellement, avec retours d'erreur clairs. |

Les pages de démonstration conservent leur rôle mais adoptent les jetons, la navigation et les composants partagés lorsque cela n'altère pas leur démonstration.

## Comportement et données

La refonte ne modifie ni routes API, ni authentification, ni stockage local, ni contrats TypeScript. Les appels API existants, les permissions et les pièces jointes du chat sont conservés. Les nouveaux composants reçoivent des données déjà disponibles dans les pages; ils affichent un état vide ou indisponible lorsque l'API ne répond pas.

## Accessibilité et responsive

- Navigation, boutons et panneaux utilisables au clavier avec un focus visible.
- Contrôles iconiques avec libellé accessible.
- Menu mobile fermé avec `Escape` et focus contenu dans son contexte.
- Contenus critiques ne reposant jamais sur la couleur seule.
- Vérification à 360 px, 768 px, 1024 px et 1440 px; aucune barre horizontale.

## Plan de modification ciblé

- Mettre à jour `frontend/app/globals.css` et `frontend/lib/theme.ts` pour les jetons et styles de base.
- Introduire les composants partagés dans `frontend/components/` et moderniser `Sidebar.tsx`.
- Recomposer les pages produit dans `frontend/app/` sans changer leurs échanges avec le backend.
- Préserver les pages de démo, puis harmoniser leur chrome et leurs états communs si nécessaire.

## Vérification

1. `npx tsc --noEmit` passe sans erreur.
2. `npm run build` produit le site statique sans erreur.
3. Vérification visuelle de `/`, `/agents`, `/chat`, `/memory`, `/tools` et `/login` aux quatre largeurs prévues.
4. Test manuel : connexion, envoi de message, pièce jointe, thème, navigation clavier et menu mobile.

## Hors périmètre

- Toute modification du backend Python, de l'orchestration, des modèles IA ou des routes API.
- Changement de marque, logo ou nom de package.
- Ajout d'une dépendance UI ou d'un service externe.
