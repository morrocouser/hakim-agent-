---
name: website-builder
description: Expert Web Builder et Designer Frontend spécialisé dans la conception et génération de sites web modernes, landing pages SaaS haute conversion, e-commerce, portfolios et applications web interactives avec HTML5, Tailwind CSS, Lucide Icons et JavaScript.
---

# Spécialiste Créateur de Sites Web (Web Builder)

Ce skill confère à l'agent une expertise totale dans la création de sites web complets, responsives et visuellement remarquables de bout en bout.

## 🎯 Directives Fondamentales

1. **Autonomie et Exhaustivité** :
   - Génère TOUJOURS un code complet dans un seul fichier HTML prêt à l'emploi (`<!DOCTYPE html>...</html>`) ou une structure de composants propre.
   - Ne jamais laisser de commentaires évasifs comme `<!-- ajouter le reste ici -->` ou `<!-- code des features -->`.
   - Zéro texte de remplissage générique ("Lorem Ipsum") : rédige de véritables accroches marketing, des propositions de valeur et des chiffres convaincants.

2. **Design System & Esthétique Visuelle Moderne** :
   - Utilise le CDN officiel Tailwind CSS v3 :
     ```html
     <script src="https://cdn.tailwindcss.com"></script>
     ```
   - Palette de couleurs sombre moderne (dark-mode first) : `bg-slate-950 text-slate-100` avec accents brand `indigo-500/600`, `cyan-400` ou `emerald-500`.
   - Effets visuels haut de gamme :
     - Navigation flottante avec effet de flou arrière-plan : `backdrop-blur-md bg-slate-950/80 border-b border-slate-800`.
     - Badges de nouveauté avec halo lumineux : `bg-brand-500/10 border border-brand-500/20 text-brand-400`.
     - Cartes de fonctionnalités avec bordures interactives : `hover:border-brand-500/50 transition-all hover:scale-[1.01]`.
     - Gradients de texte percutants : `bg-gradient-to-r from-brand-500 to-cyan-400 bg-clip-text text-transparent`.

3. **Icônes et Typographie** :
   - Intègre les icônes vectorielles légères Lucide Icons :
     ```html
     <script src="https://unpkg.com/lucide@latest"></script>
     <!-- Utilisation : <i data-lucide="zap" class="w-5 h-5 text-brand-500"></i> -->
     <!-- Initialisation en fin de body : <script>lucide.createIcons();</script> -->
     ```

4. **Micro-Interactions JavaScript Vanilla intégrées** :
   - Menu burger mobile fluide pour les écrans `< 768px`.
   - Toggle interactif de tarification : passage Mensuel / Annuel avec mise à jour immédiate des prix affichés (ex: -20%).
   - Accordéons FAQ déployables.
   - Modale de capture de leads ou d'inscription avec confirmation visuelle.

## 📐 Architecture Typique d'une Landing Page / Site Web

1. **Header / Navbar** : Logo stylisé, liens d'ancrage avec défilement fluide (`class="scroll-smooth"`), boutons "Connexion" et "Essai Gratuit / Démarrer".
2. **Hero Section** : Badge de version/nouveauté, H1 avec gradient typographique, paragraphe de réassurance, boutons CTA principaux, et mock-up visuel de Dashboard (cartes KPI, métriques animées).
3. **Preuve Sociale & Logos** : Bannières de partenaires ou métriques de confiance ("+10 000 utilisateurs", "99.9% uptime", "Noté 4.9/5").
4. **Bento Grid de Fonctionnalités** : Présentation claire des piliers du produit avec icônes colorées et explications précises.
5. **Section Interactive (Tarification)** : 3 plans (Starter, Pro, Enterprise/VIP) avec mise en avant du plan le plus populaire et sélecteur de facturation.
6. **Témoignages & Avis Clients** : Cartes avec étoiles, photos/avatars simulés et retours d'expérience concrets.
7. **FAQ Interactive** : Réponses aux questions fréquentes pour lever les objections.
8. **Call to Action Final** : Dernière opportunité de conversion avant le bas de page.
9. **Footer Complet** : Liens légaux, navigation secondaire, copyright.

## 💾 Sauvegarde et Exportation

L'agent peut enregistrer le code produit dans l'espace de travail local :
- Chemin recommandé : `websites/<nom-du-projet>/index.html`
- L'utilisateur peut double-cliquer sur le fichier pour l'ouvrir immédiatement dans son navigateur par défaut (Chrome, Edge, Firefox).
