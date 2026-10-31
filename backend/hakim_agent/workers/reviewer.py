"""
HakimAgent - Agent 3: Reviewer / Tester Worker (Étape 3)
Inspiré d'AutoGen (GroupChat Critic) et LangGraph (Human/Critic in the loop).

Lit le résultat retourné par l'Executor (ou un autre worker), vérifie
qu'il n'y a pas d'erreur de syntaxe, d'exception ou de bug critique,
et donne son feu vert ou fournit un feedback de correction.
"""

from __future__ import annotations

import ast
import re
from typing import Any, Dict, Optional, Tuple

from hakim_agent.workers.base import BaseWorker
from hakim_agent.state import AgentState


class ReviewerWorker(BaseWorker):
    """
    Agent spécialisé dans la validation, le test de syntaxe et la détection d'anomalies (@qa_reviewer).
    """

    name: str = "@qa_reviewer"
    role: str = "qa_reviewer"
    alias: str = "agent_reviewer"
    description: str = "Validation finale, contrôle qualité (QA), test de syntaxe et conformité."
    requires_review: bool = False

    def __init__(self, llm_client: Optional[Any] = None):
        if llm_client is None:
            try:
                from axiom.claude.client import LocalAPIClient
                client = LocalAPIClient()
                self.llm_client = client if client.is_configured() else None
            except Exception:
                self.llm_client = None
        else:
            self.llm_client = llm_client

    def check(self, result: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Vérifie le résultat d'une exécution.
        Retourne (is_valid: bool, feedback: str).
        """
        if not isinstance(result, dict):
            return False, "Le résultat fourni n'est pas un dictionnaire structuré valide."

        # 1. Vérification du succès global
        if not result.get("success", False):
            stderr = result.get("stderr", "") or result.get("output", "")
            return False, f"Échec d'exécution détecté : {stderr}"

        # 2. Vérification du code de sortie système
        exit_code = result.get("exit_code", 0)
        if exit_code != 0:
            return False, f"Code de sortie d'erreur ({exit_code}). Erreur : {result.get('stderr', '')}"

        # 3. Vérification de la syntaxe Python si du code est présent
        code = result.get("code")
        language = result.get("language", "")
        if code and language == "python":
            try:
                ast.parse(code)
            except SyntaxError as e:
                return False, f"Erreur de syntaxe Python ligne {e.lineno}: {e.msg}"

        # 4. Détection d'exceptions non interceptées dans la sortie
        output = str(result.get("output", "")) + " " + str(result.get("stdout", ""))
        exception_match = re.search(r"(Traceback \(most recent call last\)|(\w+Error: .*))", output)
        if exception_match:
            return False, f"Trace d'exception détectée : {exception_match.group(0)}"

        # Tout est valide
        return True, "Validation réussie : syntaxe correcte, sortie propre sans exception."

    async def execute(
        self,
        step: str,
        context: Dict[str, Any],
        state: Optional[AgentState] = None,
    ) -> Dict[str, Any]:
        """Peut aussi être invoqué comme étape autonome de synthèse/review."""
        # Si appelé directement sur le contexte
        last_step_key = list(context.keys())[-1] if context else None
        last_result = context.get(last_step_key) if last_step_key else {}
        is_valid, feedback = self.check(last_result if isinstance(last_result, dict) else {"output": last_result, "success": True})

        if is_valid and self.llm_client and any(w in step.lower() for w in ["valider le résultat", "cohérence", "mathématique", "vérifier la logique"]):
            try:
                from hakim_agent.omniroute_service import omniroute_hub
                model = omniroute_hub.get_best_model_for_role("reviewer")
                resp = await self.llm_client.chat(
                    model=model,
                    system="Tu es l'Agent Reviewer de HakimAgent (expert en QA et logique mathématique). Réponds en 1 phrase concise confirmant si le résultat est cohérent ou s'il y a un problème.",
                    messages=[{"role": "user", "content": f"Instruction : {step}\nRésultat obtenu : {last_result}"}],
                    max_tokens=200,
                )
                feedback += f" | Audit [{model}] : {resp.strip()}"
            except Exception:
                pass

        return {
            "success": is_valid,
            "agent": self.name,
            "role": self.role,
            "is_valid": is_valid,
            "feedback": feedback,
            "output": f"Feu vert accordé : {feedback}" if is_valid else f"Rejet : {feedback}",
        }
