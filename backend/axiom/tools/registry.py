from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Optional
from pydantic import BaseModel


@dataclass
class ToolContext:
    """Contexte d'exécution transmis à tous les outils.

    read_only=False : les outils en écriture sont autorisés.
    read_only=True  : tout outil en écriture renvoie une erreur (aucun prompt).
    """
    read_only: bool = False
    web_search: Any = None
    file_manager: Any = None
    code_executor: Any = None
    error_log: Any = None
    memory: Any = None


@dataclass
class ToolResult:
    """Résultat d'un outil. ``text`` est inséré tel quel dans la conversation."""
    ok: bool = True
    text: str = ""
    error: str = ""


_REGISTRY: dict[str, dict] = {}


def axiom_tool(
    name: str,
    description: str,
    permissions: str = "read",
    schema: Optional[type[BaseModel]] = None,
    available: Optional[Callable[[ToolContext], bool]] = None,
) -> Callable:
    """Décorateur : enregistre un outil dans le registre central."""
    def decorator(handler: Callable) -> Callable:
        _REGISTRY[name] = {
            "name": name,
            "description": description,
            "permissions": permissions,   # "read" | "write"
            "schema": schema,
            "available": available,
            "handler": handler,
        }
        return handler
    return decorator


def get_tools() -> list[dict]:
    """Retourne les métadonnées (sans handler) de tous les outils enregistrés."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "permissions": t["permissions"],
            "parameters": t["schema"].model_json_schema() if t["schema"] else {"type": "object", "properties": {}},
        }
        for t in _REGISTRY.values()
    ]


def build_tools_spec(ctx: Optional[ToolContext] = None) -> list[dict]:
    """Construit la liste de tools au format OpenAI (function calling).

    Les outils dont ``available`` est défini et rend False pour un contexte
    donné sont exclus. Les outils en écriture restent présents même en
    """
    spec = []
    for meta in _REGISTRY.values():
        if meta.get("available") and ctx and not meta["available"](ctx):
            continue
        schema = meta["schema"].model_json_schema() if meta["schema"] else {"type": "object", "properties": {}}
        spec.append({
            "type": "function",
            "function": {
                "name": meta["name"],
                "description": meta["description"],
                "parameters": schema,
            },
        })
    return spec


async def invoke_tool(name: str, params: dict, ctx: Optional[ToolContext] = None) -> ToolResult:
    """Invoque un outil enregistré, avec validation Pydantic et permission."""
    ctx = ctx or ToolContext()
    meta = _REGISTRY.get(name)
    if not meta:
        return ToolResult(ok=False, error=f"Outil inconnu: {name}")
    if ctx.read_only and meta["permissions"] == "write":
        return ToolResult(ok=False, error=f"Outil en écriture bloqué (lecture seule): {name}")
    if meta.get("available") and not meta["available"](ctx):
        return ToolResult(ok=False, error=f"Outil indisponible: {name}")
    try:
        if meta["schema"] is not None:
            validated = meta["schema"].model_validate(params or {})
        else:
            validated = params
        result = meta["handler"](validated, ctx)
        if inspect.isawaitable(result):
            result = await result
        return ToolResult(ok=True, text=str(result))
    except Exception as e:
        return ToolResult(ok=False, error=f"[Tool {name}] {e}")