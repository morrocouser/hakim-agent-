"""Tool Protocol — Système d'outils inspiré de Claude Code.

Architecture:
- Tool: Protocol définissant l'interface de tous les outils
- ToolResult: Résultat structuré avec type, métadonnées, temps d'exécution
- ToolPermission: Niveaux de permission (READ, WRITE, EXECUTE, DESTRUCTIVE)
- ToolSchema: Validation JSON Schema des entrées
- ToolCategory: Organisation catégorielle des outils
"""

from __future__ import annotations

import time
import json
import inspect
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol, runtime_checkable
from pydantic import BaseModel


# ─── Permissions ────────────────────────────────────────────────────────────

class ToolPermission(str, Enum):
    """Niveaux de permission hiérarchiques (inspiré Claude Code)."""
    READ = "read"           # Lecture seule (grep, glob, read_file)
    WRITE = "write"         # Écriture (create_file, edit_file)
    EXECUTE = "execute"     # Exécution (bash, code_execute)
    DESTRUCTIVE = "destructive"  # Actions irréversibles (delete_file, drop_table)

    def __ge__(self, other):
        order = [self.READ, self.WRITE, self.EXECUTE, self.DESTRUCTIVE]
        return order.index(self) >= order.index(other)

    def __gt__(self, other):
        order = [self.READ, self.WRITE, self.EXECUTE, self.DESTRUCTIVE]
        return order.index(self) > order.index(other)


# ─── Tool Result ────────────────────────────────────────────────────────────

class ToolResultType(str, Enum):
    """Types de contenu dans un résultat d'outil."""
    TEXT = "text"
    CODE = "code"
    JSON = "json"
    ERROR = "error"
    IMAGE = "image"
    MARKDOWN = "markdown"


@dataclass
class ToolResult:
    """Résultat structuré d'un outil (inspiré Claude Code ToolResult)."""
    ok: bool = True
    content: str = ""
    type: ToolResultType = ToolResultType.TEXT
    metadata: dict = field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: str = ""
    truncated: bool = False
    source: str = ""  # Nom de l'outil qui a généré le résultat

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "content": self.content,
            "type": self.type.value,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "truncated": self.truncated,
            "source": self.source,
        }

    def to_tool_message(self) -> str:
        """Format pour message tool dans la conversation."""
        if not self.ok:
            return f"[Tool Error] {self.error}"
        if self.type == ToolResultType.JSON:
            return self.content
        return self.content


# ─── Tool Schema ────────────────────────────────────────────────────────────

@dataclass
class ToolSchema:
    """Schéma JSON d'un outil (inspiré Claude Code input_schema)."""
    name: str
    description: str
    parameters: dict = field(default_factory=lambda: {"type": "object", "properties": {}})
    required: list[str] = field(default_factory=list)
    examples: list[dict] = field(default_factory=list)

    def to_openai_format(self) -> dict:
        """Convertit au format OpenAI function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def validate(self, params: dict) -> list[str]:
        """Valide les paramètres contre le schéma. Retourne les erreurs."""
        errors = []
        for req in self.required:
            if req not in params:
                errors.append(f"Paramètre manquant: {req}")
        return errors


# ─── Tool Protocol ──────────────────────────────────────────────────────────

@runtime_checkable
class Tool(Protocol):
    """Protocol définissant l'interface de tous les outils (inspiré Claude Code)."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def permission(self) -> ToolPermission: ...

    @property
    def schema(self) -> ToolSchema: ...

    async def execute(self, params: Optional[dict] = None, context: Optional[dict] = None, **kwargs) -> ToolResult: ...

    def is_available(self, context: dict) -> bool: ...


# ─── Base Tool ──────────────────────────────────────────────────────────────

class BaseTool:
    """Classe de base pour tous les outils APEX (inspiré Claude Code Tool)."""

    _name: str = ""
    _description: str = ""
    _permission: ToolPermission = ToolPermission.READ
    _schema: Optional[ToolSchema] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def permission(self) -> ToolPermission:
        return self._permission

    @property
    def schema(self) -> ToolSchema:
        if self._schema is None:
            raise ValueError(f"Tool {self._name} must define _schema")
        return self._schema

    async def execute(self, params: Optional[dict] = None, context: Optional[dict] = None, **kwargs) -> ToolResult:
        """Point d'entrée principal avec timing automatique."""
        start = time.time()
        merged_params = dict(params) if isinstance(params, dict) else {}
        if kwargs:
            merged_params.update(kwargs)
        ctx = context if isinstance(context, dict) else {}
        try:
            res_or_coro = self._execute(merged_params, ctx)
            if inspect.isawaitable(res_or_coro):
                result = await res_or_coro
            else:
                result = res_or_coro
            result.execution_time_ms = (time.time() - start) * 1000
            result.source = self._name
            return result
        except Exception as e:
            return ToolResult(
                ok=False,
                error=f"[{self._name}] {str(e)}",
                type=ToolResultType.ERROR,
                execution_time_ms=(time.time() - start) * 1000,
                source=self._name,
            )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        """Implémentation spécifique de l'outil (à surcharger)."""
        raise NotImplementedError

    def is_available(self, context: dict) -> bool:
        """Vérifie si l'outil est disponible dans le contexte donné."""
        return True

    def to_spec(self) -> dict:
        """Convertit en spécification OpenAI."""
        return self.schema.to_openai_format()


# ─── Tool Registry ──────────────────────────────────────────────────────────

class ToolRegistry:
    """Registre central des outils avec discovery dynamique (inspiré Claude Code)."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, tool: BaseTool, category: str = "general") -> None:
        """Enregistre un outil dans le registre."""
        self._tools[tool.name] = tool
        if category not in self._categories:
            self._categories[category] = []
        if tool.name not in self._categories[category]:
            self._categories[category].append(tool.name)

    def get(self, name: str) -> Optional[BaseTool]:
        """Récupère un outil par son nom."""
        return self._tools.get(name)

    def all_tools(self) -> list[BaseTool]:
        """Retourne tous les outils enregistrés."""
        return list(self._tools.values())

    def by_category(self, category: str) -> list[BaseTool]:
        """Retourne les outils d'une catégorie."""
        names = self._categories.get(category, [])
        return [self._tools[n] for n in names if n in self._tools]

    def available_tools(self, context: dict, min_permission: ToolPermission = ToolPermission.READ) -> list[BaseTool]:
        """Retourne les outils disponibles selon le contexte et les permissions."""
        result = []
        for tool in self._tools.values():
            if tool.permission >= min_permission and tool.is_available(context):
                result.append(tool)
        return result

    def build_spec(self, context: dict, min_permission: ToolPermission = ToolPermission.READ) -> list[dict]:
        """Construit la spec OpenAI pour le function calling."""
        return [tool.to_spec() for tool in self.available_tools(context, min_permission)]

    def categories(self) -> list[str]:
        """Retourne les catégories disponibles."""
        return list(self._categories.keys())


# ─── Global Registry ────────────────────────────────────────────────────────

_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Retourne le registre global."""
    return _registry


def register_tool(tool: BaseTool, category: str = "general") -> None:
    """Enregistre un outil dans le registre global."""
    _registry.register(tool, category)
