"""Axiom CLI Engine — Moteur Agentique de Code (Style Claude Code).

Ce module fournit l'orchestration autonome de code en terminal :
1. Détection et chargement de CLAUDE.md / AXIOM.md.
2. Prise d'instantanés (snapshots) et annulation (rollback / undo).
3. Compaction dynamique de l'historique de conversation.
4. Système de permissions interactif (lecture/écriture/bash).
5. Boucle Agentique d'exécution d'outils (Prompt -> Tool -> Result -> Loop).
"""

from __future__ import annotations

import os
import shutil
import time
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple


# ─── 1. Snapshot & Rollback Manager ──────────────────────────────────────

class SnapshotManager:
    """Gère la sauvegarde temporaire des fichiers avant édition pour le rollback (Undo)."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.snapshot_dir = self.project_root / ".axiom" / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.stack: List[Dict[str, str]] = []  # List of {"original_path": str, "backup_path": str, "timestamp": str}

    def capture(self, file_path: str) -> Optional[str]:
        """Prend un instantané du fichier avant modification."""
        target = Path(file_path)
        if not target.is_absolute():
            target = (self.project_root / target).resolve()

        if not target.exists() or not target.is_file():
            # Nouveau fichier : marquer comme création
            snapshot_entry = {
                "original_path": str(target),
                "backup_path": "",
                "is_new": "true",
                "timestamp": str(time.time()),
            }
            self.stack.append(snapshot_entry)
            return None

        # Fichier existant : copier dans .axiom/snapshots/
        ts = int(time.time() * 1000)
        safe_name = f"{ts}_{target.name}.bak"
        backup_path = self.snapshot_dir / safe_name
        shutil.copy2(target, backup_path)

        entry = {
            "original_path": str(target),
            "backup_path": str(backup_path),
            "is_new": "false",
            "timestamp": str(ts),
        }
        self.stack.append(entry)
        return str(backup_path)

    def rollback(self) -> Tuple[bool, str]:
        """Annule la dernière modification de fichier (Undo)."""
        if not self.stack:
            return False, "Aucun snapshot disponible à restaurer."

        last = self.stack.pop()
        orig = Path(last["original_path"])

        if last.get("is_new") == "true":
            if orig.exists():
                orig.unlink()
            return True, f"Fichier créé supprimé (rollback): {orig.name}"

        backup = Path(last["backup_path"])
        if not backup.exists():
            return False, f"Fichier de sauvegarde introuvable: {backup}"

        shutil.copy2(backup, orig)
        backup.unlink(missing_ok=True)
        return True, f"Fichier restauré (rollback): {orig.name}"


# ─── 2. Context Manager & Compaction ─────────────────────────────────────

class ContextManager:
    """Gère le prompt système, le chargement de CLAUDE.md et la compaction."""

    def __init__(self, project_root: str, max_tokens: int = 12000):
        self.project_root = Path(project_root).resolve()
        self.max_tokens = max_tokens

    def load_system_prompt(self) -> str:
        """Construit le prompt système initial avec auto-détection de CLAUDE.md / AXIOM.md."""
        base_prompt = (
            "Tu es un assistant agentique de développement de code de niveau expert (style Claude Code / Cursor).\n"
            "Tu interagis directement avec le système de fichiers et le terminal local pour inspecter, tester et modifier le code.\n"
            "Directives de fonctionnement :\n"
            "1. Utilise 'read_file' pour inspecter les fichiers pertinents avant d'éditer.\n"
            "2. Utilise 'edit_file' avec remplacement exact 'old_text' -> 'new_text' pour des modifications ciblées.\n"
            "3. Utilise 'write_file' pour créer de nouveaux fichiers.\n"
            "4. Utilise 'bash' pour lancer des commandes shell, tests et builds.\n"
            "5. Réponds de manière concise, précise et professionnelle en français.\n"
        )

        # Auto-détection de CLAUDE.md ou AXIOM.md
        rules = []
        for filename in ["CLAUDE.md", "AXIOM.md", ".claude/instructions.md"]:
            path = self.project_root / filename
            if path.exists() and path.is_file():
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    rules.append(f"--- Règles du Projet ({filename}) ---\n{content}")
                except Exception:
                    pass

        if rules:
            base_prompt += "\n\n" + "\n\n".join(rules)

        return base_prompt

    def estimate_tokens(self, history: List[Dict[str, Any]]) -> int:
        """Estime le nombre de tokens dans l'historique."""
        char_count = sum(len(str(m.get("content", ""))) for m in history)
        return char_count // 4

    def compact_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compacte l'historique lorsque la limite de contexte est approchée.

        - Tronque les réponses d'outils volumineuses.
        - Synthétise les échanges intermédiaires passés.
        """
        if len(history) <= 4:
            return history

        compacted: List[Dict[str, Any]] = []
        # Conserver le premier message utilisateur
        compacted.append(history[0])

        # Résumé des étapes intermédiaires
        actions_summary = []
        middle_messages = history[1:-3]

        for m in middle_messages:
            role = m.get("role")
            content = str(m.get("content", ""))
            if role == "tool" or "tool_calls" in m:
                first_line = content.splitlines()[0] if content else ""
                actions_summary.append(first_line[:100])
            elif role == "assistant":
                actions_summary.append(content[:120])

        summary_text = (
            "[Système: Historique compacté automatique]\n"
            "Résumé des étapes précédentes effectuées par l'agent :\n" +
            "\n".join(f"- {s}" for s in actions_summary[:10])
        )
        compacted.append({"role": "system", "content": summary_text})

        # Conserver les 3 derniers messages intacts
        compacted.extend(history[-3:])
        return compacted


# ─── 3. Axiom Agentic CLI Engine ──────────────────────────────────────────

class AxiomCLIEngine:
    """Moteur principal de l'agentic CLI."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.snapshots = SnapshotManager(str(self.project_root))
        self.context_mgr = ContextManager(str(self.project_root))
        self.system_prompt = self.context_mgr.load_system_prompt()
        self.history: List[Dict[str, Any]] = []
        self.auto_approve: bool = False
        self.selected_model: str = "claude-3-7-sonnet"

        # Importer les outils built-in
        from axiom.tools.builtin import (
            ReadTool, WriteTool, EditTool, GlobTool, GrepTool, BashTool
        )
        self.tools = {
            "read_file": ReadTool(str(self.project_root)),
            "write_file": WriteTool(str(self.project_root)),
            "edit_file": EditTool(str(self.project_root)),
            "glob": GlobTool(str(self.project_root)),
            "grep": GrepTool(str(self.project_root)),
            "bash": BashTool(str(self.project_root)),
        }

    def generate_diff(self, file_path: str, old_str: str, new_str: str) -> str:
        """Génère un diff unifié affichable dans le terminal."""
        diff_lines = list(difflib.unified_diff(
            old_str.splitlines(keepends=True),
            new_str.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        ))
        return "".join(diff_lines)

    async def execute_tool_call(
        self,
        name: str,
        args: Dict[str, Any],
        permission_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None
    ) -> Tuple[bool, str]:
        """Exécute un outil avec vérification de sécurité et snapshot."""
        if name not in self.tools:
            return False, f"Outil inconnu : {name}"

        tool = self.tools[name]

        # 1. Vérification des permissions pour modification / shell
        if name in ["write_file", "edit_file", "bash"] and not self.auto_approve:
            # Fail-closed : sans callback de confirmation, l'action est refusée.
            if not permission_callback:
                return False, f"Action '{name}' refusée : aucune confirmation utilisateur disponible."
            if not permission_callback(name, args):
                return False, f"Action '{name}' refusée par l'utilisateur."

        # 2. Instantané préalable pour write_file / edit_file
        if name in ["write_file", "edit_file"] and "path" in args:
            self.snapshots.capture(args["path"])

        # 3. Exécution de l'outil
        try:
            result = await tool.execute(args, context={"project_root": str(self.project_root)})
            if result.ok:
                return True, result.content
            else:
                return False, result.error or "Erreur inconnue de l'outil"
        except Exception as e:
            return False, f"Erreur lors de l'exécution de {name}: {e}"

    def rollback(self) -> Tuple[bool, str]:
        """Annule la dernière modification."""
        return self.snapshots.rollback()

    def clear(self):
        """Réinitialise l'historique."""
        self.history.clear()

    def compact(self) -> int:
        """Compacte l'historique."""
        before = len(self.history)
        self.history = self.context_mgr.compact_history(self.history)
        after = len(self.history)
        return before - after
