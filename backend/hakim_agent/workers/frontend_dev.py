"""
HakimAgent - Worker Spécialisé : Frontend Developer (@frontend_dev)
Implémente les composants de code (React, Vue, Tailwind CSS, TypeScript/JS)
en s'appuyant rigoureusement sur les spécifications transmises par l'UX Designer.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from hakim_agent.workers.base import BaseWorker
from hakim_agent.state import AgentState


class FrontendDevWorker(BaseWorker):
    """
    Agent spécialisé dans le développement d'interfaces et de composants frontend.
    Consomme les tokens et spécifications du contexte pour générer du code propre.
    """

    name: str = "@frontend_dev"
    role: str = "frontend_dev"
    description: str = "Développeur frontend spécialisé React, Tailwind CSS, HTML/JS et composants réutilisables."
    requires_review: bool = True  # Soumis à la validation du QA Reviewer

    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client

    async def execute(
        self,
        step: str,
        context: Dict[str, Any],
        state: Optional[AgentState] = None,
    ) -> Dict[str, Any]:
        """
        Génère le code du composant en utilisant les spécifications UI/UX déjà présentes dans le contexte.
        """
        # 1. Extraction du contexte UX précédent
        ux_spec = None
        for step_name, step_result in context.items():
            if isinstance(step_result, dict) and (
                step_result.get("agent") == "@ux_designer" or "design_tokens" in step_result
            ):
                ux_spec = step_result
                break

        tokens = ux_spec.get("design_tokens", {}) if ux_spec else {}
        theme = tokens.get("theme", "dark" if "sombre" in step.lower() else "light")
        tailwind = tokens.get("tailwind_classes", {})

        theme_classes = tailwind.get(
            "theme_classes",
            "bg-zinc-900 hover:bg-zinc-800 text-white border border-zinc-700/50 shadow-sm"
            if theme == "dark"
            else "bg-zinc-100 hover:bg-zinc-200 text-zinc-900 border border-zinc-300",
        )
        spacing_classes = tailwind.get("spacing_classes", "px-4 py-2 rounded-md text-sm")
        container_classes = tailwind.get("container", "inline-flex items-center justify-center font-medium transition-colors")

        full_classes = f"{container_classes} {spacing_classes} {theme_classes}"

        # Code React/TypeScript du composant
        component_code = (
            'import React from "react";\n\n'
            'interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {\n'
            '  label?: string;\n'
            '  children?: React.ReactNode;\n'
            '}\n\n'
            'export const DarkMinimalButton: React.FC<ButtonProps> = ({\n'
            '  label = "Action",\n'
            '  children,\n'
            '  className = "",\n'
            '  ...props\n'
            '}) => {\n'
            '  return (\n'
            f'    <button className="{full_classes} ' + '${className}" {...props}>\n'
            '      {children || label}\n'
            '    </button>\n'
            '  );\n'
            '};\n\n'
            'export default DarkMinimalButton;\n'
        )

        return {
            "success": True,
            "agent": self.name,
            "role": self.role,
            "language": "typescript",
            "framework": "react",
            "code": component_code,
            "inherited_ux_spec": bool(ux_spec),
            "output": f"Composant frontend généré avec succès ({len(component_code)} caractères, classes: {full_classes}).",
        }
