"""Bridge — Connecte l'ancien système de registre au nouveau protocole Tool.

Permet d'utiliser les outils legacy (tool_wrappers.py) avec le nouveau système.
"""

from __future__ import annotations

from typing import Any, Optional
from axiom.tools.base import (
    BaseTool, ToolResult, ToolResultType, ToolPermission,
    ToolSchema, get_registry,
)
from axiom.tools.registry import ToolContext, _REGISTRY


class LegacyToolBridge(BaseTool):
    """Adapte un outil legacy au nouveau protocole Tool."""

    def __init__(self, name: str, meta: dict):
        self._name = name
        self._description = meta["description"]
        self._permission = (
            ToolPermission.WRITE if meta["permissions"] == "write" else ToolPermission.READ
        )
        self._meta = meta
        self._schema = ToolSchema(
            name=name,
            description=meta["description"],
            parameters=meta["schema"].model_json_schema() if meta.get("schema") else {"type": "object", "properties": {}},
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        import inspect

        handler = self._meta["handler"]
        schema = self._meta.get("schema")

        try:
            if schema is not None:
                validated = schema.model_validate(params)
            else:
                validated = params

            ctx = context.get("_legacy_context", ToolContext())
            result = handler(validated, ctx)

            if inspect.isawaitable(result):
                result = await result

            return ToolResult(
                ok=True,
                content=str(result),
                type=ToolResultType.TEXT,
            )
        except Exception as e:
            return ToolResult(
                ok=False,
                error=f"[{self._name}] {e}",
                type=ToolResultType.ERROR,
            )


def bridge_legacy_tools(ctx: Optional[ToolContext] = None) -> None:
    """Enregistre tous les outils legacy dans le nouveau registre."""
    registry = get_registry()

    for name, meta in _REGISTRY.items():
        if name not in [t.name for t in registry.all_tools()]:
            bridge = LegacyToolBridge(name, meta)
            registry.register(bridge, "legacy")
