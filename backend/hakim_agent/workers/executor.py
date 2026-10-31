"""
HakimAgent - Agent 1: Code / Exec Worker (Étape 3)
Inspiré de Smolagents (Hugging Face) et Open Interpreter.

Exécute du code localement ou dans un bac à sable contrôlé,
capture stdout/stderr, respecte des garde-fous de sécurité et applique
des correctifs lors des boucles de feedback.
"""

from __future__ import annotations

import ast
import asyncio
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from hakim_agent.workers.base import BaseWorker
from hakim_agent.state import AgentState
from hakim_agent.omniroute_service import omniroute_hub


# Modèles de commandes ou motifs dangereux à bloquer
BLOCKED_PATTERNS = [
    r"rm\s+(-rf|-r|-f)\s+[/~]",
    r"format\s+[a-zA-Z]:?",
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",  # fork bomb
    r"dd\s+if=.*of=/dev/sd",
    r"chmod\s+-R\s+777\s+/",
    r"mkfs",
]


class CodeExecutorWorker(BaseWorker):
    """
    Agent spécialisé dans la génération, l'exécution et la correction de code.
    Dispose d'un interpréteur sécurisé (Python / Subprocess).
    """

    name: str = "agent_code_executor"
    role: str = "code_exec"
    description: str = "Exécuteur de code Python et commandes système contrôlées (Smolagents / Open Interpreter style)."
    requires_review: bool = True  # Toujours soumis à vérification

    def __init__(
        self,
        timeout_seconds: int = 30,
        allowed_languages: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
        llm_client: Optional[Any] = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.allowed_languages = allowed_languages or ["python", "bash", "powershell"]
        self.working_dir = working_dir or os.getcwd()

        if llm_client is None:
            try:
                from axiom.claude.client import LocalAPIClient
                client = LocalAPIClient()
                self.llm_client = client if client.is_configured() else None
            except Exception:
                self.llm_client = None
        else:
            self.llm_client = llm_client

    def _is_safe(self, code_or_cmd: str) -> tuple[bool, Optional[str]]:
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, code_or_cmd, re.IGNORECASE):
                return False, f"Commande potentiellement destructrice détectée: motif '{pattern}' bloqué."
        return True, None

    def _extract_code(self, text: str) -> str:
        """Extrait un bloc de code ```python ou ```bash s'il existe, sinon nettoie et utilise le texte brut."""
        # 1. Supprimer les balises de réflexion des modèles de raisonnement (<think>...</think>)
        clean = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        
        # 2. Supprimer les lignes d'en-tête de sécurité ou de commentaires préliminaires
        clean = re.sub(r"^(?:User Safety|Safety Check|Note|Thought):\s*[^\n]*\n", "", clean.strip(), flags=re.IGNORECASE)
        
        code_match = re.search(r"```(?:python|py)?\s*\n(.*?)```", clean, re.DOTALL | re.IGNORECASE)
        if code_match:
            return code_match.group(1).strip()
        bash_match = re.search(r"```(?:bash|sh|powershell)?\s*\n(.*?)```", clean, re.DOTALL | re.IGNORECASE)
        if bash_match:
            return bash_match.group(1).strip()
        return clean.strip()

    async def execute(
        self,
        step: str,
        context: Dict[str, Any],
        state: Optional[AgentState] = None,
    ) -> Dict[str, Any]:
        """Exécute une instruction de code ou un script Python extrait."""
        start_time = time.time()
        
        # 1. Vérification PRIORITAIRE des garde-fous de sécurité sur le texte reçu
        is_safe, error_msg = self._is_safe(step)
        if not is_safe:
            return {
                "success": False,
                "code": step,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": -1,
                "execution_time_ms": 0,
                "language": "security",
                "output": f"Sécurité : {error_msg}",
            }

        code = self._extract_code(step)
        is_safe_code, error_code_msg = self._is_safe(code)
        if not is_safe_code:
            return {
                "success": False,
                "code": code,
                "stdout": "",
                "stderr": error_code_msg,
                "exit_code": -1,
                "execution_time_ms": 0,
                "language": "security",
                "output": f"Sécurité : {error_code_msg}",
            }

        # 2. Détection: est-ce une consigne en langage naturel ou du code direct?
        is_instruction = any(
            re.match(rf"^\s*(?:\d+[\.\)]\s*)?{verb}\b", code, re.IGNORECASE)
            for verb in ["écrire", "écris", "write", "calcule", "calculer", "calculate", "générer", "génère", "generate", "créer", "crée", "create", "résoudre", "solve", "trouve", "trouver"]
        )

        is_python = False
        if not is_instruction:
            try:
                ast.parse(code)
                is_python = True
            except SyntaxError:
                # Si le code contient des mots-clés typiques de syntaxe Python, on le traite comme du code à exécuter
                if any(kw in code for kw in ["def ", "import ", "class ", "return ", "lambda ", "async def "]):
                    is_python = True

        # 3. Si c'est une consigne ou non exécutable directement et qu'un LLM est configuré,
        # on génère le code Python d'action (style Smolagents Code-as-Action)
        if (not is_python or is_instruction) and self.llm_client and hasattr(self.llm_client, "chat") and getattr(self.llm_client, "is_configured", lambda: True)():
            first_word = code.strip().split()[0].lower() if code.strip() else ""
            common_shell_cmds = {"dir", "ls", "cd", "pwd", "cat", "echo", "mkdir", "rmdir", "cp", "mv", "git", "powershell", "cmd"}
            if is_instruction or (first_word not in common_shell_cmds and not is_python):
                try:
                    system_prompt = (
                        "Tu es l'Agent Code Executor de HakimAgent (style Smolagents/Open Interpreter).\n"
                        "Génère UNIQUEMENT un bloc de code Python pour accomplir la tâche suivante.\n"
                        "N'ajoute aucun bavardage, salutations ni texte avant/après. Renvoie uniquement le code.\n"
                        "Le code doit être autonome, propre et faire un print() explicite du résultat final."
                    )
                    active_model = omniroute_hub.get_best_model_for_role("executor")
                    generated = await self.llm_client.chat(
                        model=active_model,
                        system=system_prompt,
                        messages=[{"role": "user", "content": f"Tâche : {step}\nContexte partagé : {context}"}],
                        max_tokens=800,
                    )
                    extracted = self._extract_code(generated)
                    if extracted and extracted != generated:
                        code = extracted
                    else:
                        code = generated.replace("```python", "").replace("```", "").strip()
                    is_python = True
                except Exception:
                    pass

            # Re-contrôle de sécurité sur le code généré
            is_safe_gen, err_gen = self._is_safe(code)
            if not is_safe_gen:
                return {
                    "success": False,
                    "code": code,
                    "stdout": "",
                    "stderr": err_gen,
                    "exit_code": -1,
                    "execution_time_ms": 0,
                    "language": "security",
                    "output": f"Sécurité : {err_gen}",
                }

        if is_python:
            return await self._run_python_code(code, start_time)
        else:
            return await self._run_shell_cmd(code, start_time)

    async def _run_python_code(self, code: str, start_time: float) -> Dict[str, Any]:
        """Exécute un bloc Python dans un processus isolé."""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
        try:
            temp_file.write(code)
            temp_file.close()

            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                temp_file.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=float(self.timeout_seconds),
                )
                stdout = stdout_data.decode("utf-8", errors="replace").strip()
                stderr = stderr_data.decode("utf-8", errors="replace").strip()
                exit_code = proc.returncode or 0
            except asyncio.TimeoutError:
                proc.kill()
                stdout = ""
                stderr = f"Timeout d'exécution dépassé ({self.timeout_seconds}s)"
                exit_code = 124

            elapsed_ms = int((time.time() - start_time) * 1000)
            success = (exit_code == 0 and not stderr)

            return {
                "success": success,
                "code": code,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "execution_time_ms": elapsed_ms,
                "language": "python",
                "output": stdout if success else (stderr or f"Exit code {exit_code}"),
            }
        finally:
            if os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

    async def _run_shell_cmd(self, command: str, start_time: float) -> Dict[str, Any]:
        """Exécute une commande système contrôlée."""
        shell_cmd = command.strip()
        is_windows = sys.platform == "win32"
        shell = "powershell" if is_windows else "bash"
        args = ["powershell", "-NoProfile", "-Command", shell_cmd] if is_windows else ["bash", "-c", shell_cmd]

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=float(self.timeout_seconds),
                )
                stdout = stdout_data.decode("utf-8", errors="replace").strip()
                stderr = stderr_data.decode("utf-8", errors="replace").strip()
                exit_code = proc.returncode or 0
            except asyncio.TimeoutError:
                proc.kill()
                stdout = ""
                stderr = f"Timeout shell dépassé ({self.timeout_seconds}s)"
                exit_code = 124

            elapsed_ms = int((time.time() - start_time) * 1000)
            success = (exit_code == 0)

            return {
                "success": success,
                "code": command,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "execution_time_ms": elapsed_ms,
                "language": shell,
                "output": stdout if success else (stderr or f"Exit code {exit_code}"),
            }
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "code": command,
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "execution_time_ms": elapsed_ms,
                "language": shell,
                "output": str(e),
            }

    async def fix(
        self,
        step: str,
        result: Dict[str, Any],
        feedback: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Corrige le code suite au rejet du Reviewer.
        Intègre le feedback pour patcher la syntaxe ou sollicite le LLM si configuré.
        """
        previous_code = result.get("code", "")
        corrected_code = previous_code

        # 1. Tentative d'auto-correction via LLM si disponible
        if self.llm_client and hasattr(self.llm_client, "chat") and getattr(self.llm_client, "is_configured", lambda: True)():
            try:
                system_prompt = (
                    "Tu es l'Agent Code Executor de HakimAgent en boucle de correction.\n"
                    "Le code précédent a échoué ou a été rejeté par le Reviewer.\n"
                    "Fournis UNIQUEMENT le code Python corrigé, prêt à être exécuté avec print() du résultat."
                )
                active_model = omniroute_hub.get_best_model_for_role("executor")
                repaired = await self.llm_client.chat(
                    model=active_model,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Tâche : {step}\nCode ayant échoué :\n```python\n{previous_code}\n```\nFeedback d'erreur :\n{feedback}\nContexte : {context}",
                        }
                    ],
                    max_tokens=800,
                )
                extracted = self._extract_code(repaired)
                if extracted and extracted != repaired:
                    corrected_code = extracted
                else:
                    corrected_code = repaired.replace("```python", "").replace("```", "").strip()
            except Exception:
                pass

        # 2. Si non corrigé par LLM, correctifs heuristiques
        if corrected_code == previous_code and ("SyntaxError" in feedback or "NameError" in feedback):
            for var in re.findall(r"name '(\w+)' is not defined", feedback):
                if var in context:
                    corrected_code = f"{var} = {repr(context[var])}\n" + corrected_code
                else:
                    corrected_code = f"{var} = None\n" + corrected_code

        # Re-tente l'exécution avec le code patché
        patch_result = await self.execute(corrected_code, context)
        patch_result["applied_fix_for"] = feedback
        return patch_result
