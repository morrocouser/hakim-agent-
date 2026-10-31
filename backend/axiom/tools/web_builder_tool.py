"""
AXIOM v4.0 — Outil Dédié Créateur de Sites Web (WebBuilderTool).
Permet à l'agent AGENT_WEB_BUILDER de scaffolder des sites complets,
d'exporter des pages HTML5/Tailwind prêtes à l'emploi et de sauvegarder
des projets interactifs dans le répertoire 'websites/'.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from axiom.logging_setup import log
from axiom.tools.base import (
    BaseTool,
    ToolPermission,
    ToolResult,
    ToolResultType,
    ToolSchema,
)

TEMPLATES_CATALOG = {
    "saas_landing": {
        "name": "SaaS Landing Page (AutoDS/Linear style)",
        "description": "Landing page SaaS moderne avec hero animé, mockup de dashboard, toggle de prix mensuel/annuel et preuve sociale.",
        "recommended_colors": ["indigo", "cyan", "slate-950"],
    },
    "ecommerce_store": {
        "name": "Boutique E-commerce Moderne (Shopify/Dropship style)",
        "description": "Vitrine e-commerce avec grille de produits, badges promos, panier slide-over interactif et avis vérifiés.",
        "recommended_colors": ["emerald", "amber", "slate-900"],
    },
    "creative_portfolio": {
        "name": "Portfolio Développeur / Designer",
        "description": "Portfolio haut de gamme avec dark mode, bento-grid de projets, timeline d'expérience et formulaire de contact.",
        "recommended_colors": ["purple", "pink", "slate-950"],
    },
    "ai_waitlist": {
        "name": "AI App Waitlist & Lead Gen",
        "description": "Page de capture épurée avec input email interactif, compteur de places et animation de lueur (glow effect).",
        "recommended_colors": ["blue", "violet", "slate-900"],
    },
    "analytics_dashboard": {
        "name": "Dashboard & Cockpit Web Interactif",
        "description": "Interface web de tableau de bord avec sidebar rétractable, cartes KPI, tableau de données et graphiques SVG.",
        "recommended_colors": ["sky", "teal", "slate-950"],
    },
}


class WebBuilderTool(BaseTool):
    """Outil de génération, sauvegarde et inspection de sites web modernes."""

    _name = "web_builder"
    _description = (
        "Outil expert pour la création de sites web complets (HTML5, Tailwind CSS, JavaScript). "
        "Permet de lister les templates disponibles, générer des architectures de sites et "
        "sauvegarder automatiquement des fichiers 'index.html' directement dans l'espace de travail."
    )
    _permission = ToolPermission.WRITE

    def __init__(self, base_dir: str = "."):
        self._base_dir = Path(base_dir).resolve()
        self._websites_dir = self._base_dir / "websites"
        self._websites_dir.mkdir(parents=True, exist_ok=True)

        self._schema = ToolSchema(
            name=self._name,
            description=self._description,
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list_templates", "save_site", "scaffold"],
                        "description": "Action à effectuer",
                    },
                    "site_name": {
                        "type": "string",
                        "description": "Nom du dossier du site (ex: 'mon-saas-autods')",
                    },
                    "template": {
                        "type": "string",
                        "description": "Type de template (saas_landing, ecommerce_store, creative_portfolio, ai_waitlist, analytics_dashboard)",
                    },
                    "html_content": {
                        "type": "string",
                        "description": "Contenu HTML5/Tailwind complet à enregistrer",
                    },
                },
                "required": ["action"],
            },
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        action = params.get("action", "list_templates")

        if action == "list_templates":
            data = {
                "total_templates": len(TEMPLATES_CATALOG),
                "templates": TEMPLATES_CATALOG,
                "target_directory": str(self._websites_dir),
            }
            return ToolResult(
                ok=True,
                content=json.dumps(data, indent=2, ensure_ascii=False),
                type=ToolResultType.JSON,
                metadata=data,
            )

        elif action == "save_site":
            site_name = params.get("site_name", "nouveau-site")
            html_content = params.get("html_content", "")
            if not html_content:
                return ToolResult(
                    ok=False,
                    content="",
                    type=ToolResultType.ERROR,
                    error="Le paramètre 'html_content' est obligatoire pour sauvegarder un site.",
                )

            safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "", site_name.strip().replace(" ", "-")) or "mon-site-web"
            site_folder = self._websites_dir / safe_name
            site_folder.mkdir(parents=True, exist_ok=True)
            index_file = site_folder / "index.html"
            index_file.write_text(html_content, encoding="utf-8")

            abs_path = str(index_file.resolve())
            file_url = f"file:///{abs_path.replace(os.sep, '/')}"

            log.info("🌐 [WebBuilderTool] Site enregistré: %s", abs_path)
            data = {
                "status": "success",
                "message": f"Site web '{safe_name}' créé et enregistré avec succès.",
                "relative_path": f"websites/{safe_name}/index.html",
                "absolute_path": abs_path,
                "browser_url": file_url,
                "bytes": len(html_content.encode("utf-8")),
            }
            return ToolResult(
                ok=True,
                content=json.dumps(data, indent=2, ensure_ascii=False),
                type=ToolResultType.JSON,
                metadata=data,
            )

        elif action == "scaffold":
            template_key = params.get("template", "saas_landing")
            site_name = params.get("site_name", "nouveau-site")
            template_info = TEMPLATES_CATALOG.get(template_key, TEMPLATES_CATALOG["saas_landing"])

            base_scaffold = f"""<!DOCTYPE html>
<html lang="fr" class="scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{site_name.replace('-', ' ').title()} - {template_info['name']}</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Lucide Icons CDN -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          colors: {{
            brand: {{ 50: '#eef2ff', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' }}
          }}
        }}
      }}
    }}
  </script>
</head>
<body class="bg-slate-950 text-slate-100 font-sans antialiased min-h-screen">
  <!-- NAVBAR -->
  <nav class="fixed top-0 w-full z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <i data-lucide="zap" class="w-7 h-7 text-brand-500 fill-brand-500"></i>
        <span class="text-xl font-bold tracking-wide">{site_name.replace('-', ' ').title()}</span>
      </div>
      <div class="hidden md:flex space-x-8 text-sm font-medium text-slate-300">
        <a href="#features" class="hover:text-white transition">Fonctionnalités</a>
        <a href="#pricing" class="hover:text-white transition">Tarifs</a>
      </div>
      <a href="#pricing" class="bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition">
        Commencer
      </a>
    </div>
  </nav>

  <!-- HERO SECTION -->
  <section class="pt-36 pb-20 px-6 text-center max-w-5xl mx-auto">
    <span class="bg-brand-500/10 text-brand-500 border border-brand-500/20 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider inline-block mb-4">
      {template_info['name']}
    </span>
    <h1 class="text-4xl md:text-6xl font-extrabold text-white leading-tight mb-6">
      Votre Plateforme Web de Nouvelle Génération
    </h1>
    <p class="text-lg text-slate-400 max-w-2xl mx-auto mb-8">
      {template_info['description']}
    </p>
    <div class="flex flex-col sm:flex-row justify-center gap-4">
      <a href="#pricing" class="bg-brand-600 hover:bg-brand-500 text-white px-8 py-3.5 rounded-xl font-semibold transition shadow-lg shadow-brand-600/30">
        Essayer Gratuitement
      </a>
      <a href="#features" class="bg-slate-900 hover:bg-slate-800 border border-slate-800 text-white px-8 py-3.5 rounded-xl font-semibold transition">
        Découvrir
      </a>
    </div>
  </section>

  <script>
    lucide.createIcons();
  </script>
</body>
</html>"""
            data = {
                "status": "success",
                "template": template_key,
                "scaffold_html": base_scaffold,
            }
            return ToolResult(
                ok=True,
                content=json.dumps(data, indent=2, ensure_ascii=False),
                type=ToolResultType.JSON,
                metadata=data,
            )

        return ToolResult(
            ok=False,
            content="",
            type=ToolResultType.ERROR,
            error=f"Action inconnue: {action}",
        )
