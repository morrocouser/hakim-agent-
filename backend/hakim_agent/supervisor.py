"""
HakimAgent - Agent Superviseur / Routeur (Étape 2)
Pattern Hub & Spokes / Superviseur centralisé.

Le Superviseur ne fait aucun travail technique direct :
1. Il analyse la demande de l'utilisateur.
2. Il la découpe en un plan d'étapes ordonnées (create_plan / create_plan_async via LLM ou heuristique).
3. Il désigne pour chaque étape quel agent spécialisé doit intervenir (route_step) :
   - @ux_designer : Conception UI/UX, ergonomie, tokens et wireframes.
   - @frontend_dev : Implémentation de composants de code (React, HTML, Tailwind).
   - @qa_reviewer : Contrôle qualité, tests de syntaxe et revue de code.
   - ResearcherWorker : Recherche web, documentation et scraping.
   - CodeExecutorWorker : Interpréteur et sandbox Python/système.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from hakim_agent.workers.base import BaseWorker
from hakim_agent.workers.executor import CodeExecutorWorker
from hakim_agent.workers.researcher import ResearcherWorker
from hakim_agent.workers.reviewer import ReviewerWorker
from hakim_agent.workers.ux_designer import UXDesignerWorker
from hakim_agent.workers.frontend_dev import FrontendDevWorker
from hakim_agent.omniroute_service import omniroute_hub


class SupervisorAgent:
    """
    Superviseur / Routeur central de HakimAgent.
    Orchestre le routage vers les spécialistes sans exécuter d'actions techniques directement.
    """

    def __init__(
        self,
        executor: Optional[CodeExecutorWorker] = None,
        researcher: Optional[ResearcherWorker] = None,
        reviewer: Optional[ReviewerWorker] = None,
        ux_designer: Optional[UXDesignerWorker] = None,
        frontend_dev: Optional[FrontendDevWorker] = None,
        llm_client: Optional[Any] = None,
    ):
        if llm_client is False:
            self.llm_client = None
        elif llm_client is None:
            try:
                from axiom.claude.client import LocalAPIClient
                client = LocalAPIClient()
                self.llm_client = client if client.is_configured() else None
            except Exception:
                self.llm_client = None
        else:
            self.llm_client = llm_client

        self.executor = executor or CodeExecutorWorker(llm_client=self.llm_client)
        self.researcher = researcher or ResearcherWorker()
        self.reviewer = reviewer or ReviewerWorker(llm_client=self.llm_client)
        self.qa_reviewer = self.reviewer
        self.ux_designer = ux_designer or UXDesignerWorker(llm_client=self.llm_client)
        self.frontend_dev = frontend_dev or FrontendDevWorker(llm_client=self.llm_client)

    def create_plan(self, prompt: str) -> List[str]:
        """
        Découpage heuristique déterministe instantané (offline-friendly).
        """
        clean_prompt = prompt.strip()
        
        # Découpage si l'utilisateur a déjà fourni une liste
        bullet_steps = re.findall(r"(?:^|\n)\s*(?:\d+[\.\)]|\-|\*)\s*(.+)", clean_prompt)
        if len(bullet_steps) >= 2:
            return [s.strip() for s in bullet_steps if s.strip()]

        lower_prompt = clean_prompt.lower()
        plan: List[str] = []

        # 1. Pipeline Multi-Agents complet (UI/UX -> Frontend Dev -> QA Reviewer)
        has_design = any(w in lower_prompt for w in ["conçois", "concois", "design", "ui", "ux", "wireframe", "maquette", "@ux_designer"])
        has_frontend = any(w in lower_prompt for w in ["code", "programme", "script", "composant", "bouton", "frontend", "@frontend_dev"])
        has_review = any(w in lower_prompt for w in ["vérifie", "verifier", "teste", "tester", "valide", "valider", "review", "contrôle", "@qa_reviewer"])

        if has_design and has_frontend and has_review:
            plan.append(f"Concevoir le design et les spécifications UI/UX pour : {clean_prompt}")
            plan.append(f"Coder le composant frontend d'après les spécifications pour : {clean_prompt}")
            plan.append("Vérifier et valider le code du composant")
            return plan

        # 2. Cas spécifique UI/UX uniquement
        if has_design and not has_frontend and not has_review:
            plan.append(f"Concevoir l'interface et les spécifications UI/UX pour : {clean_prompt}")
            return plan

        # 3. Cas spécifique Composant Frontend uniquement
        if (has_frontend or "@frontend_dev" in lower_prompt) and not has_design and not has_review and any(w in lower_prompt for w in ["composant", "frontend", "bouton", "react", "html", "css", "tailwind", "@frontend_dev"]):
            plan.append(f"Développer le composant de code pour : {clean_prompt}")
            return plan

        # 4. Pipelines standards (Recherche, Code Python, etc.)
        needs_research = any(w in lower_prompt for w in ["cherche", "recherche", "api", "doc", "trouve", "trouver", "scrape", "web", "comparatif", "article", "articles"])
        needs_code = any(w in lower_prompt for w in ["code", "script", "programme", "python", "exécute", "calcule", "affiche", "implémente"])

        if needs_research and needs_code:
            plan.append(f"Rechercher les informations nécessaires pour : {clean_prompt}")
            plan.append(f"Écrire et exécuter le code Python pour : {clean_prompt}")
            plan.append("Vérifier et valider le résultat final")
        elif needs_code:
            plan.append(f"Générer et exécuter le script pour : {clean_prompt}")
            plan.append("Vérifier l'absence d'erreurs et valider l'exécution")
        elif needs_research:
            plan.append(f"Rechercher et extraire les données pour : {clean_prompt}")
            plan.append("Synthétiser et valider les informations obtenues")
        else:
            plan.append(clean_prompt)

        return plan

    async def create_plan_async(self, prompt: str) -> List[str]:
        """
        Découpage assisté par LLM (Gemini / Google AI Studio ou OpenRouter) avec repli heuristique.
        """
        clean_prompt = prompt.strip().lower()
        has_design = any(w in clean_prompt for w in ["conçois", "concois", "design", "ui", "ux", "wireframe", "maquette", "@ux_designer"])
        has_frontend = any(w in clean_prompt for w in ["code", "programme", "script", "composant", "bouton", "frontend", "@frontend_dev"])
        has_review = any(w in clean_prompt for w in ["vérifie", "verifier", "teste", "tester", "valide", "valider", "review", "contrôle", "@qa_reviewer"])

        # Priorité aux modèles spécialisés direct (pipeline complet 3 agents ou rôles ciblés)
        if (has_design and has_frontend and has_review) or (has_design and not has_frontend) or (has_frontend and not has_design and not has_review and "composant" in clean_prompt):
            return self.create_plan(prompt)

        if self.llm_client and hasattr(self.llm_client, "chat") and getattr(self.llm_client, "is_configured", lambda: True)():
            try:
                system_prompt = (
                    "Tu es le Superviseur de HakimAgent (architecture Hub & Spokes).\n"
                    "Décompose la requête utilisateur en un plan de 2 à 4 étapes concrètes, ordonnées et concises.\n"
                    "Chaque étape doit commencer par un verbe d'action clair (ex: 'Rechercher...', 'Écrire et exécuter le code...', 'Vérifier...').\n"
                    "Réponds UNIQUEMENT sous forme de liste numérotée (1. ...\n2. ...), sans texte d'introduction ni conclusion."
                )
                active_model = omniroute_hub.get_best_model_for_role("supervisor")
                resp = await self.llm_client.chat(
                    model=active_model,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=350,
                )
                lines = [re.sub(r"^\d+[\.\)]\s*", "", line).strip() for line in resp.strip().split("\n") if line.strip()]
                steps = [l for l in lines if len(l) > 3 and not l.startswith("```")]
                if len(steps) >= 2:
                    return steps
            except Exception:
                pass

        return self.create_plan(prompt)

    def route_step(self, step: str) -> BaseWorker:
        """
        Désigne le spécialiste compétent pour l'étape donnée :
        - @ux_designer : UI/UX, Wireframe, Ergonomie
        - @frontend_dev : Composants Frontend, Code UI, React, HTML/CSS
        - @qa_reviewer : Tests, Revue de code, Validation, Contrôle
        - ResearcherWorker : Web, Scraping, Doc, Recherche
        - CodeExecutorWorker : Script Python, Calcul, Exécution
        """
        s = step.lower()

        # Priorité 1 : Mentions explicites d'agents
        if "@ux_designer" in s:
            return self.ux_designer
        if "@frontend_dev" in s:
            return self.frontend_dev
        if "@qa_reviewer" in s:
            return self.qa_reviewer

        # Priorité 2 : Review / Validation / QA
        if any(w in s for w in ["vérifier", "verifier", "teste", "tester", "valider", "review", "syntaxe", "contrôle", "qa"]):
            return self.qa_reviewer

        # Priorité 3 : UI / UX Design
        if any(w in s for w in ["concevoir", "conçois", "concois", "ui/ux", " ui ", " ux ", "wireframe", "maquette", "design", "ergonomie", "tokens"]) and not any(w in s for w in ["coder", "code python", "exécuter"]):
            return self.ux_designer

        # Priorité 4 : Frontend Dev / Composant de code
        if any(w in s for w in ["coder le composant", "composant frontend", "composant de code", "react", "vue", "tailwind", "html/css"]) or (any(w in s for w in ["composant", "bouton"]) and any(w in s for w in ["code", "coder", "développer", "developper"])):
            return self.frontend_dev

        # Priorité 5 : Web / Data / Recherche
        if any(w in s for w in ["recherche", "rechercher", "cherche", "chercher", "trouve", "trouver", "web", "api", "scrape", "doc", "documentation", "article", "articles", "http", "url"]):
            return self.researcher

        # Priorité 6 : Code Python / Exécution système par défaut
        if any(w in s for w in ["code", "python", "script", "exécute", "execute", "calcul", "bash", "print", "def ", "class ", "run"]):
            return self.executor

        if "```" in step:
            return self.executor

        return self.executor
