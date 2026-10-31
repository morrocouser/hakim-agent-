---
name: web-site-builder
description: Skill de création et d'architecture de sites web pour HakimAgent / APEX v4.0. Fournit des outils pour concevoir, générer du code HTML5/Tailwind/React, créer des composants UI et prévisualiser en direct.
version: 1.0.0
author: HakimAgent Team
license: MIT
tools:
  - web_scaffold
  - web_generate_page
  - component_builder
  - web_preview
  - export_website
triggers:
  - site
  - website
  - web
  - landing page
  - frontend
  - html
  - css
  - tailwind
  - react
  - ui
examples:
  - name: Créer une landing page SaaS
    description: Génère une landing page complète avec hero, fonctionnalités, tarifs et formulaire
    input: """
    intent: Création site web SaaS
    template: modern-saas
    sections: ["hero", "features", "pricing", "contact"]
    """
    output: """
    {
      "success": true,
      "files": ["index.html", "styles.css", "script.js"],
      "preview_url": "file:///workspace/site/index.html"
    }
    """
entry_points:
  web_scaffold: web_tools:web_scaffold
  web_generate_page: web_tools:web_generate_page
  component_builder: web_tools:component_builder
  web_preview: web_tools:web_preview
  export_website: web_tools:export_website
---

# Web Site Builder Skill

Ce skill permet à l'agent spécialisé **Elena WebCraft** (et à l'orchestrateur) de concevoir et générer des sites web complets, responsives et modernes.

## Fonctionnalités Principales

- **Scaffolding de Site (`web_scaffold`)**: Initialise la structure complète d'un projet web avec HTML5 sémantique, Tailwind CSS moderne (CDN ou modules), scripts et polices Google Web Fonts.
- **Générateur de Page (`web_generate_page`)**: Conçoit une page web intégrale (Landing page, Portfolio, E-commerce vitrine, Blog, Dashboard) avec design premium glassmorphism, responsive mobile-first et palette de couleurs adaptée.
- **Constructeur de Composants (`component_builder`)**: Génère des blocs autonomes : Navbar sticky, Hero Section dynamique, Grille de cartes fonctionnalités, Tableau de prix comparatif, Témoignages et Footer.
- **Aperçu Live (`web_preview`)**: Prépare l'aperçu du site pour le conteneur virtuel de l'agent et met à jour l'écran partagé en direct.
- **Exportation (`export_website`)**: Archive et exporte le bundle de fichiers vers `user_files/websites/`.
