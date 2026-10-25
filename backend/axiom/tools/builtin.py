"""Built-in Tools — Outils core inspirés de Claude Code.

Ces outils suivent le protocole Tool et sont enregistrés automatiquement.
"""

from __future__ import annotations

import os
import glob
import re
from pathlib import Path
from typing import Optional

from axiom.tools.base import (
    BaseTool, ToolResult, ToolResultType, ToolPermission,
    ToolSchema, register_tool,
)


# ─── ReadTool ───────────────────────────────────────────────────────────────

class ReadTool(BaseTool):
    """Lit le contenu d'un fichier (inspiré Claude Code ReadTool)."""

    _name = "read_file"
    _description = "Lit le contenu d'un fichier. Retourne le texte avec numéros de lignes."
    _permission = ToolPermission.READ

    def __init__(self, base_dir: str = "."):
        self._base_dir = Path(base_dir).resolve()
        self._schema = ToolSchema(
            name=self._name,
            description=self._description,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Chemin du fichier à lire",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Ligne de départ (1-indexed)",
                        "default": 0,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Nombre max de lignes",
                        "default": 2000,
                    },
                },
                "required": ["path"],
            },
            required=["path"],
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        requested_path = Path(params["path"])
        if requested_path.is_absolute():
            path = requested_path.resolve()
        else:
            path = (self._base_dir / requested_path).resolve()

        try:
            path.relative_to(self._base_dir)
        except ValueError:
            return ToolResult(ok=False, error=f"[Erreur de Sécurité] Accès refusé : Tentative de Path Traversal en dehors de {self._base_dir}", type=ToolResultType.ERROR)

        if not path.exists():
            return ToolResult(ok=False, error=f"Fichier non trouvé: {path}", type=ToolResultType.ERROR)

        if not path.is_file():
            return ToolResult(ok=False, error=f"Ce n'est pas un fichier: {path}", type=ToolResultType.ERROR)

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            offset = params.get("offset", 0)
            limit = params.get("limit", 2000)

            sliced = lines[offset:offset + limit]
            numbered = [f"{i + offset + 1}: {line}" for i, line in enumerate(sliced)]
            result_content = "\n".join(numbered)

            truncated = (offset + limit) < len(lines)
            return ToolResult(
                ok=True,
                content=result_content,
                type=ToolResultType.TEXT,
                metadata={"path": str(path), "total_lines": len(lines), "offset": offset, "limit": limit},
                truncated=truncated,
            )
        except Exception as e:
            return ToolResult(ok=False, error=f"Erreur lecture: {e}", type=ToolResultType.ERROR)


# ─── WriteTool ──────────────────────────────────────────────────────────────

class WriteTool(BaseTool):
    """Écrit un fichier (inspiré Claude Code WriteTool)."""

    _name = "write_file"
    _description = "Écrit le contenu dans un fichier. Crée le fichier s'il n'existe pas, écrase s'il existe."
    _permission = ToolPermission.WRITE

    def __init__(self, base_dir: str = "."):
        self._base_dir = Path(base_dir).resolve()
        self._schema = ToolSchema(
            name=self._name,
            description=self._description,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Chemin du fichier à écrire",
                    },
                    "content": {
                        "type": "string",
                        "description": "Contenu à écrire",
                    },
                },
                "required": ["path", "content"],
            },
            required=["path", "content"],
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        requested_path = Path(params["path"])
        if requested_path.is_absolute():
            path = requested_path.resolve()
        else:
            path = (self._base_dir / requested_path).resolve()

        try:
            path.relative_to(self._base_dir)
        except ValueError:
            return ToolResult(ok=False, error=f"[Erreur de Sécurité] Accès refusé : Tentative de Path Traversal en dehors de {self._base_dir}", type=ToolResultType.ERROR)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(params["content"], encoding="utf-8")
            return ToolResult(
                ok=True,
                content=f"Fichier écrit: {path} ({len(params['content'])} caractères)",
                type=ToolResultType.TEXT,
                metadata={"path": str(path), "bytes_written": len(params["content"])},
            )
        except Exception as e:
            return ToolResult(ok=False, error=f"Erreur écriture: {e}", type=ToolResultType.ERROR)


# ─── EditTool ───────────────────────────────────────────────────────────────

class EditTool(BaseTool):
    """Édite un fichier avec remplacement exact (inspiré Claude Code EditTool)."""

    _name = "edit_file"
    _description = "Remplace un texte exact dans un fichier par un nouveau texte."
    _permission = ToolPermission.WRITE

    def __init__(self, base_dir: str = "."):
        self._base_dir = Path(base_dir).resolve()
        self._schema = ToolSchema(
            name=self._name,
            description=self._description,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Chemin du fichier à éditer",
                    },
                    "old_text": {
                        "type": "string",
                        "description": "Texte exact à remplacer",
                    },
                    "new_text": {
                        "type": "string",
                        "description": "Nouveau texte de remplacement",
                    },
                },
                "required": ["path", "old_text", "new_text"],
            },
            required=["path", "old_text", "new_text"],
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        requested_path = Path(params["path"])
        if requested_path.is_absolute():
            path = requested_path.resolve()
        else:
            path = (self._base_dir / requested_path).resolve()

        try:
            path.relative_to(self._base_dir)
        except ValueError:
            return ToolResult(ok=False, error=f"[Erreur de Sécurité] Accès refusé : Tentative de Path Traversal en dehors de {self._base_dir}", type=ToolResultType.ERROR)

        if not path.exists():
            return ToolResult(ok=False, error=f"Fichier non trouvé: {path}", type=ToolResultType.ERROR)

        try:
            content = path.read_text(encoding="utf-8")
            old_text = params["old_text"]
            new_text = params["new_text"]

            if old_text not in content:
                return ToolResult(ok=False, error=f"Texte non trouvé dans {path}", type=ToolResultType.ERROR)

            count = content.count(old_text)
            if count > 1:
                return ToolResult(ok=False, error=f"Plusieurs occurrences ({count}) — soyez plus spécifique", type=ToolResultType.ERROR)

            new_content = content.replace(old_text, new_text, 1)
            path.write_text(new_content, encoding="utf-8")

            return ToolResult(
                ok=True,
                content=f"Fichier édité: {path}",
                type=ToolResultType.TEXT,
                metadata={"path": str(path), "old_length": len(old_text), "new_length": len(new_text)},
            )
        except Exception as e:
            return ToolResult(ok=False, error=f"Erreur édition: {e}", type=ToolResultType.ERROR)


# ─── BashTool ───────────────────────────────────────────────────────────────

class BashTool(BaseTool):
    """Exécute une commande bash (inspiré Claude Code BashTool)."""

    _name = "bash"
    _description = "Exécute une commande shell et retourne la sortie."
    _permission = ToolPermission.EXECUTE

    def __init__(self, base_dir: str = ".", timeout: int = 120):
        self._base_dir = Path(base_dir).resolve()
        self._timeout = timeout
        self._schema = ToolSchema(
            name=self._name,
            description=self._description,
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Commande shell à exécuter",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout en secondes",
                        "default": 120,
                    },
                },
                "required": ["command"],
            },
            required=["command"],
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        import asyncio

        command = params["command"]
        timeout = params.get("timeout", self._timeout)

        # Garde-fou best-effort (une liste noire reste contournable) : la vraie
        # protection est la confirmation utilisateur imposée par CLIEngine
        # (fail-closed) avant tout appel à cet outil.
        normalized = re.sub(r"\s+", " ", command)
        dangerous = [
            r"\brm\s+-\w*[rf]\w*\s+(-\w+\s+)*(/|~|\$HOME)(\s|\*|$)",
            r"\bmkfs", r":\(\)\s*\{", r"\bdd\s+if=/dev", r">\s*/dev/sd",
        ]
        for d in dangerous:
            if re.search(d, normalized):
                return ToolResult(ok=False, error="Commande dangereuse bloquée", type=ToolResultType.ERROR)

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._base_dir),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            stdout_text = stdout.decode("utf-8", errors="replace").strip()
            stderr_text = stderr.decode("utf-8", errors="replace").strip()

            output = stdout_text
            if stderr_text:
                output += f"\n[STDERR]\n{stderr_text}" if output else stderr_text

            if proc.returncode != 0:
                return ToolResult(
                    ok=True,  # On retourne ok=True mais avec le code d'erreur
                    content=output or f"Commande terminée avec code {proc.returncode}",
                    type=ToolResultType.TEXT,
                    metadata={"exit_code": proc.returncode, "command": command},
                )

            return ToolResult(
                ok=True,
                content=output or "(pas de sortie)",
                type=ToolResultType.TEXT,
                metadata={"exit_code": 0, "command": command},
            )
        except asyncio.TimeoutError:
            return ToolResult(ok=False, error=f"Timeout après {timeout}s: {command}", type=ToolResultType.ERROR)
        except Exception as e:
            return ToolResult(ok=False, error=f"Erreur bash: {e}", type=ToolResultType.ERROR)


# ─── GlobTool ───────────────────────────────────────────────────────────────

class GlobTool(BaseTool):
    """Recherche de fichiers par pattern (inspiré Claude Code GlobTool)."""

    _name = "glob"
    _description = "Recherche des fichiers correspondant à un pattern glob."
    _permission = ToolPermission.READ

    def __init__(self, base_dir: str = "."):
        self._base_dir = Path(base_dir).resolve()
        self._schema = ToolSchema(
            name=self._name,
            description=self._description,
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Pattern glob (ex: '**/*.py', 'src/**/*.ts')",
                    },
                    "path": {
                        "type": "string",
                        "description": "Répertoire de recherche (optionnel)",
                    },
                },
                "required": ["pattern"],
            },
            required=["pattern"],
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        pattern = params["pattern"]
        search_dir = params.get("path", ".")

        base = Path(search_dir)
        if not base.is_absolute():
            base = self._base_dir / base

        try:
            matches = sorted(base.glob(pattern))
            files = [str(m.relative_to(self._base_dir)) for m in matches if m.is_file()]

            if not files:
                return ToolResult(ok=True, content="Aucun fichier trouvé", type=ToolResultType.TEXT)

            return ToolResult(
                ok=True,
                content="\n".join(files),
                type=ToolResultType.TEXT,
                metadata={"pattern": pattern, "count": len(files)},
            )
        except Exception as e:
            return ToolResult(ok=False, error=f"Erreur glob: {e}", type=ToolResultType.ERROR)


# ─── GrepTool ───────────────────────────────────────────────────────────────

class GrepTool(BaseTool):
    """Recherche dans le contenu des fichiers (inspiré Claude Code GrepTool)."""

    _name = "grep"
    _description = "Recherche un pattern regex dans les fichiers."
    _permission = ToolPermission.READ

    def __init__(self, base_dir: str = "."):
        self._base_dir = Path(base_dir).resolve()
        self._schema = ToolSchema(
            name=self._name,
            description=self._description,
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Pattern regex à rechercher",
                    },
                    "path": {
                        "type": "string",
                        "description": "Répertoire ou fichier à rechercher",
                    },
                    "include": {
                        "type": "string",
                        "description": "Pattern de fichiers à inclure (ex: '*.py')",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Nombre max de résultats",
                        "default": 50,
                    },
                },
                "required": ["pattern"],
            },
            required=["pattern"],
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        pattern = params["pattern"]
        search_path = params.get("path", ".")
        include = params.get("include")
        max_results = params.get("max_results", 50)

        base = Path(search_path)
        if not base.is_absolute():
            base = self._base_dir / base

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return ToolResult(ok=False, error=f"Regex invalide: {e}", type=ToolResultType.ERROR)

        results = []
        files_searched = 0

        try:
            if base.is_file():
                files = [base]
            else:
                glob_pattern = f"**/{include}" if include else "**/*"
                files = list(base.glob(glob_pattern))

            for filepath in files:
                if not filepath.is_file():
                    continue
                files_searched += 1

                try:
                    content = filepath.read_text(encoding="utf-8", errors="replace")
                    for i, line in enumerate(content.splitlines(), 1):
                        if regex.search(line):
                            rel = filepath.relative_to(self._base_dir) if filepath.is_relative_to(self._base_dir) else filepath
                            results.append(f"{rel}:{i}: {line.strip()}")
                            if len(results) >= max_results:
                                break
                except (PermissionError, OSError):
                    continue

                if len(results) >= max_results:
                    break

            if not results:
                return ToolResult(ok=True, content="Aucune correspondance", type=ToolResultType.TEXT)

            return ToolResult(
                ok=True,
                content="\n".join(results),
                type=ToolResultType.TEXT,
                metadata={"pattern": pattern, "matches": len(results), "files_searched": files_searched},
                truncated=len(results) >= max_results,
            )
        except Exception as e:
            return ToolResult(ok=False, error=f"Erreur grep: {e}", type=ToolResultType.ERROR)


# ─── Register All Built-in Tools ────────────────────────────────────────────

def register_builtin_tools(registry=None, base_dir: str = ".") -> None:
    """Enregistre tous les outils built-in dans le registre."""
    from axiom.tools.base import get_registry
    from axiom.tools.google_services import (
        GoogleDriveTool, EmailManagerTool, YouTubeTool, GoogleSearchTool,
    )
    reg = registry or get_registry()

    tools = [
        (ReadTool(base_dir), "filesystem"),
        (WriteTool(base_dir), "filesystem"),
        (EditTool(base_dir), "filesystem"),
        (GlobTool(base_dir), "filesystem"),
        (GrepTool(base_dir), "filesystem"),
        (BashTool(base_dir), "execution"),
        (GoogleDriveTool(base_dir), "google"),
        (EmailManagerTool(base_dir), "communication"),
        (YouTubeTool(base_dir), "media"),
        (GoogleSearchTool(base_dir), "research"),
    ]

    for tool, category in tools:
        reg.register(tool, category)
