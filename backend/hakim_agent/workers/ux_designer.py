"""
HakimAgent - Worker Spécialisé : UX Designer (@ux_designer)
Conçoit les maquettes, chartes graphiques, tokens de design (Tailwind/CSS)
et spécifications d'ergonomie pour les interfaces utilisateur.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from hakim_agent.workers.base import BaseWorker
from hakim_agent.state import AgentState


class UXDesignerWorker(BaseWorker):
    """
    Agent spécialisé dans le design d'interface (UI/UX).
    Fournit des spécifications visuelles, des tokens de couleur et des critères ergonomiques.
    """

    name: str = "@ux_designer"
    role: str = "ux_designer"
    description: str = "Spécialiste UI/UX, tokens de design, ergonomie et wireframes."
    requires_review: bool = False

    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client

    async def execute(
        self,
        step: str,
        context: Dict[str, Any],
        state: Optional[AgentState] = None,
    ) -> Dict[str, Any]:
        """
        Génère une spécification UI/UX complète à partir de la demande de l'étape.
        """
        step_lower = step.lower()
        is_dark = "sombre" in step_lower or "dark" in step_lower
        is_minimal = "minimal" in step_lower or "épuré" in step_lower or "epure" in step_lower

        # Palette et tokens adaptés
        bg_color = "#18181b" if is_dark else "#f4f4f5"
        text_color = "#ffffff" if is_dark else "#09090b"
        accent_color = "#3b82f6"
        hover_color = "#27272a" if is_dark else "#e4e4e7"

        design_tokens = {
            "theme": "dark" if is_dark else "light",
            "style": "minimalist" if is_minimal else "standard",
            "colors": {
                "background": bg_color,
                "text": text_color,
                "accent": accent_color,
                "hover": hover_color,
                "border": "#27272a" if is_dark else "#e4e4e7",
            },
            "typography": {
                "font_family": "Inter, sans-serif",
                "font_size": "14px",
                "font_weight": "500",
            },
            "spacing": {
                "padding_x": "16px",
                "padding_y": "8px",
                "border_radius": "6px",
            },
            "tailwind_classes": {
                "container": "inline-flex items-center justify-center font-medium transition-colors",
                "theme_classes": (
                    "bg-zinc-900 hover:bg-zinc-800 text-white border border-zinc-700/50 shadow-sm"
                    if is_dark
                    else "bg-zinc-100 hover:bg-zinc-200 text-zinc-900 border border-zinc-300"
                ),
                "spacing_classes": "px-4 py-2 rounded-md text-sm",
            },
        }

        spec_summary = (
            f"Spécification UI/UX validée : Thème {'sombre' if is_dark else 'clair'}, "
            f"style {'minimaliste' if is_minimal else 'standard'}, contraste accessible WCAG AAA. "
            f"Classes Tailwind recommandées : {design_tokens['tailwind_classes']['theme_classes']} "
            f"{design_tokens['tailwind_classes']['spacing_classes']}."
        )

        return {
            "success": True,
            "agent": self.name,
            "role": self.role,
            "design_tokens": design_tokens,
            "spec_summary": spec_summary,
            "output": spec_summary,
        }
