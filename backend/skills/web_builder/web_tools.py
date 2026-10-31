"""
Web Site Builder Tools for HakimAgent / APEX v4.0.
Fournit les fonctions exécutables pour le scaffolding, la génération de pages HTML/Tailwind,
la construction de composants et la prévisualisation live.
"""

from __future__ import annotations
import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

WEBSITES_BASE_DIR = Path(os.getcwd()) / "user_files" / "websites"


def web_scaffold(
    site_name: str,
    template: str = "landing_page",
    target_dir: Optional[str] = None,
    theme_color: str = "cyan",
) -> Dict[str, Any]:
    """Scaffolde un site web complet avec HTML5 sémantique, Tailwind CSS et JS vanilla."""
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", site_name).lower()
    out_dir = Path(target_dir) if target_dir else WEBSITES_BASE_DIR / safe_name
    out_dir.mkdir(parents=True, exist_ok=True)

    index_html = f"""<!DOCTYPE html>
<html lang="fr" class="scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{site_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
    .glass {{ background: rgba(23, 23, 23, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }}
  </style>
</head>
<body class="bg-neutral-950 text-neutral-100 min-h-screen selection:bg-{theme_color}-500 selection:text-black">
  <!-- Navigation Bar -->
  <nav class="sticky top-0 z-50 glass px-6 py-4 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-3.5 h-3.5 rounded-full bg-{theme_color}-400 shadow-[0_0_12px_#22d3ee] animate-pulse"></div>
      <span class="font-bold text-lg text-white tracking-tight">{site_name}</span>
    </div>
    <div class="flex items-center gap-6 text-xs text-neutral-300 font-medium">
      <a href="#hero" class="hover:text-white transition">Accueil</a>
      <a href="#services" class="hover:text-white transition">Services</a>
      <a href="#about" class="hover:text-white transition">À Propos</a>
      <a href="#contact" class="hover:text-white transition">Contact</a>
      <a href="#contact" class="px-4 py-2 rounded-xl bg-{theme_color}-500 hover:bg-{theme_color}-400 text-neutral-950 font-bold transition">Nous Contacter</a>
    </div>
  </nav>

  <!-- Hero Section -->
  <header id="hero" class="py-24 px-6 text-center max-w-4xl mx-auto space-y-6">
    <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-{theme_color}-500/10 border border-{theme_color}-500/30 text-{theme_color}-400 text-xs font-mono">
      <span>●</span> Expérience Digitale Haute Performance
    </div>
    <h1 class="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
      Transformez vos idées en <span class="bg-gradient-to-r from-white via-neutral-200 to-{theme_color}-400 bg-clip-text text-transparent">réalité numérique</span>
    </h1>
    <p class="text-neutral-400 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
      Bienvenue sur {site_name}. Une plateforme innovante conçue avec passion et perfection technique par Elena WebCraft.
    </p>
    <div class="flex items-center justify-center gap-4 pt-4">
      <a href="#services" class="px-6 py-3 rounded-xl bg-{theme_color}-500 hover:bg-{theme_color}-400 text-neutral-950 font-bold text-xs transition shadow-lg shadow-{theme_color}-500/25">
        Découvrir nos solutions
      </a>
      <a href="#about" class="px-6 py-3 rounded-xl glass hover:bg-neutral-800 text-neutral-200 text-xs font-medium transition">
        En savoir plus
      </a>
    </div>
  </header>

  <!-- Features Grid -->
  <section id="services" class="py-20 px-6 max-w-6xl mx-auto">
    <div class="text-center mb-12">
      <span class="text-xs uppercase tracking-widest text-neutral-400 font-mono">Ce que nous proposons</span>
      <h2 class="text-2xl sm:text-3xl font-bold text-white mt-2">Des solutions sur mesure</h2>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="p-6 rounded-2xl glass hover:border-{theme_color}-500/50 transition duration-300">
        <div class="w-10 h-10 rounded-xl bg-{theme_color}-500/10 text-{theme_color}-400 flex items-center justify-center font-bold mb-4">01</div>
        <h3 class="text-base font-semibold text-white">Performances Éclair</h3>
        <p class="text-xs text-neutral-400 mt-2 leading-relaxed">Architecture allégée, temps de chargement instantanés et optimisation Core Web Vitals.</p>
      </div>
      <div class="p-6 rounded-2xl glass hover:border-{theme_color}-500/50 transition duration-300">
        <div class="w-10 h-10 rounded-xl bg-{theme_color}-500/10 text-{theme_color}-400 flex items-center justify-center font-bold mb-4">02</div>
        <h3 class="text-base font-semibold text-white">Design Adaptatif</h3>
        <p class="text-xs text-neutral-400 mt-2 leading-relaxed">Affichage réactif pixel-perfect sur smartphone, tablette et écran 4K.</p>
      </div>
      <div class="p-6 rounded-2xl glass hover:border-{theme_color}-500/50 transition duration-300">
        <div class="w-10 h-10 rounded-xl bg-{theme_color}-500/10 text-{theme_color}-400 flex items-center justify-center font-bold mb-4">03</div>
        <h3 class="text-base font-semibold text-white">Sécurité & Fiabilité</h3>
        <p class="text-xs text-neutral-400 mt-2 leading-relaxed">Respect des standards web modernes, conformité aux règles d'accessibilité et code propre.</p>
      </div>
    </div>
  </section>

  <!-- Contact Form -->
  <section id="contact" class="py-20 px-6 max-w-xl mx-auto">
    <div class="p-8 rounded-2xl glass space-y-4">
      <h2 class="text-xl font-bold text-white text-center">Contactez-nous</h2>
      <p class="text-xs text-neutral-400 text-center">Un projet en tête ? Écrivez-nous pour un échange personnalisé.</p>
      <form class="space-y-3 pt-2" onsubmit="event.preventDefault(); alert('Message envoyé avec succès !');">
        <div>
          <label class="block text-xs text-neutral-300 mb-1">Votre Nom</label>
          <input type="text" required placeholder="Alex Dupont" class="w-full px-3 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs text-white focus:outline-none focus:border-{theme_color}-500">
        </div>
        <div>
          <label class="block text-xs text-neutral-300 mb-1">Adresse Email</label>
          <input type="email" required placeholder="alex@domaine.com" class="w-full px-3 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs text-white focus:outline-none focus:border-{theme_color}-500">
        </div>
        <div>
          <label class="block text-xs text-neutral-300 mb-1">Votre Message</label>
          <textarea rows="3" required placeholder="Détaillez vos besoins..." class="w-full px-3 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs text-white focus:outline-none focus:border-{theme_color}-500 resize-none"></textarea>
        </div>
        <button type="submit" class="w-full py-2.5 rounded-xl bg-{theme_color}-500 hover:bg-{theme_color}-400 text-neutral-950 font-bold text-xs transition cursor-pointer">
          Envoyer la demande
        </button>
      </form>
    </div>
  </section>

  <!-- Footer -->
  <footer class="border-t border-neutral-900 py-10 px-6 text-center text-xs text-neutral-500 font-mono">
    © {datetime.now().year} {site_name} · Conçu par HakimAgent & Elena WebCraft
  </footer>
</body>
</html>
"""

    index_file = out_dir / "index.html"
    index_file.write_text(index_html, encoding="utf-8")

    return {
        "success": True,
        "site_name": site_name,
        "directory": str(out_dir),
        "index_file": str(index_file),
        "preview_url": f"file:///{str(index_file).replace(os.sep, '/')}",
        "files_created": ["index.html"],
    }


def web_generate_page(
    title: str,
    description: str,
    sections: Optional[List[str]] = None,
    theme_color: str = "cyan",
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Génère une page web spécifique avec sections modulaires."""
    sections = sections or ["hero", "features", "pricing", "contact"]
    res = web_scaffold(site_name=title, target_dir=output_path, theme_color=theme_color)
    return res


def component_builder(
    component_type: str,
    props: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Génère un composant HTML/Tailwind réutilisable."""
    props = props or {}
    comp = component_type.lower()

    if comp == "navbar":
        html = """<nav class="flex items-center justify-between px-6 py-4 bg-neutral-900/80 backdrop-blur-sm border-b border-neutral-800">
  <div class="font-bold text-white">Logo</div>
  <div class="flex items-center gap-4 text-xs text-neutral-300">
    <a href="#" class="hover:text-white">Accueil</a>
    <a href="#" class="hover:text-white">Services</a>
    <a href="#" class="hover:text-white">Contact</a>
  </div>
</nav>"""
    elif comp == "hero":
        html = """<header class="py-20 text-center max-w-3xl mx-auto px-4">
  <h1 class="text-5xl font-black text-white">Titre Principal</h1>
  <p class="mt-4 text-neutral-400 text-sm">Description du produit ou service.</p>
  <button class="mt-6 px-6 py-3 rounded-xl bg-cyan-500 text-black font-bold text-xs">Action</button>
</header>"""
    elif comp == "pricing":
        html = """<div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto px-4">
  <div class="p-6 rounded-2xl bg-neutral-900 border border-neutral-800 text-center">
    <h3 class="text-sm font-bold text-white">Starter</h3>
    <div class="text-3xl font-extrabold text-cyan-400 my-3">0 €</div>
    <p class="text-xs text-neutral-400">Pour tester le service</p>
  </div>
</div>"""
    else:
        html = f"<div class='p-4 bg-neutral-900 border border-neutral-800 rounded-xl text-white'><!-- Composant {component_type} --></div>"

    return {
        "success": True,
        "component_type": component_type,
        "html_snippet": html,
    }


def web_preview(file_path: str) -> Dict[str, Any]:
    """Valide l'existence d'un fichier et renvoie l'URL de prévisualisation."""
    p = Path(file_path)
    if not p.exists():
        return {"success": False, "error": f"Fichier {file_path} introuvable."}
    return {
        "success": True,
        "preview_url": f"file:///{str(p.resolve()).replace(os.sep, '/')}",
        "size_bytes": p.stat().st_size,
    }


def export_website(site_name: str) -> Dict[str, Any]:
    """Exporte le dossier d'un site web."""
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", site_name).lower()
    site_dir = WEBSITES_BASE_DIR / safe_name
    if not site_dir.exists():
        return {"success": False, "error": f"Le site {site_name} n'existe pas."}
    files = [str(f.relative_to(site_dir)) for f in site_dir.glob("**/*") if f.is_file()]
    return {
        "success": True,
        "site_name": site_name,
        "location": str(site_dir),
        "total_files": len(files),
        "files": files,
    }
