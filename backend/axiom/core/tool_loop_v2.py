"""Tool Loop v2 — Boucle d'exécution inspirée de Claude Code.

Utilise le nouveau protocole Tool au lieu du vieux système.
Supporte:
- Tool calls avec validation
- Permission checking
- Execution context riche
- Streaming tool results
"""

from __future__ import annotations

import json
import time
from typing import Optional

from axiom.tools.base import (
    ToolRegistry, ToolResult, ToolPermission, get_registry,
)
from axiom.tools.builtin import register_builtin_tools
from axiom.tools.bridge import bridge_legacy_tools
from axiom.logging_setup import log

DEFAULT_MAX_STEPS = 8
MAX_MESSAGES = 32


def truncate_messages(messages: list[dict]) -> list[dict]:
    """Garder le premier message utilisateur + les derniers MAX_MESSAGES."""
    if len(messages) <= MAX_MESSAGES:
        return messages
    head = [m for m in messages if m.get("role") == "user"][:1]
    tail = messages[1:]
    limit = MAX_MESSAGES - len(head)
    return head + tail[-limit:]


def _assistant_with_tool_calls(resp: dict, calls: list[dict]) -> dict:
    return {
        "role": "assistant",
        "content": resp.get("content") or "",
        "tool_calls": [
            {
                "id": c["id"],
                "type": "function",
                "function": {"name": c["name"], "arguments": json.dumps(c["arguments"], ensure_ascii=False)},
            }
            for c in calls
        ],
    }


async def run_tool_loop_v2(
    claude,
    model: str,
    system: str,
    user_prompt: str,
    context: Optional[dict] = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    base_dir: str = ".",
) -> str:
    """Boucle d'exécution d'outils v2 (inspirée Claude Code).

    Args:
        claude: Client LLM
        model: Nom du modèle
        system: Prompt système
        user_prompt: Prompt utilisateur
        context: Contexte d'exécution (peut contenir des instances existantes)
        max_steps: Nombre max d'itérations
        base_dir: Répertoire de base pour les outils filesystem

    Returns:
        Texte final produit par le LLM
    """
    ctx = context or {}

    # Initialiser le registre avec les outils built-in
    registry = get_registry()
    if not registry.all_tools():
        log.info("   🔧 Initialisation du Tool Registry v2...")
        register_builtin_tools(registry, base_dir)
        bridge_legacy_tools()
        log.info("   🔧 %s outils enregistrés", len(registry.all_tools()))

    # Construire la spec OpenAI
    tools = registry.build_spec(ctx)
    messages = [{"role": "user", "content": user_prompt}]

    log.info("   🔧 Tool Loop v2 démarré — %s outils disponibles, max %s steps", len(tools), max_steps)

    if not tools:
        log.info("   🔧 Aucun outil disponible — fallback sur chat simple")
        return await claude.chat(model=model, system=system, messages=messages)

    for step in range(max_steps):
        t_step = time.time()
        log.info("   🔧 Step %s/%s...", step + 1, max_steps)

        resp = await claude.chat_with_tools(
            model=model, system=system, messages=messages, tools=tools,
        )

        if resp.get("error"):
            log.warning("   ⚠️  LLM a refusé le function calling — fallback chat simple")
            return await claude.chat(model=model, system=system, messages=messages)

        calls = resp.get("tool_calls") or []
        if not calls:
            elapsed = round(time.time() - t_step, 2)
            log.info("   ✅ Tool Loop terminé en %ss — pas de tool calls", elapsed)
            return resp.get("content") or ""

        messages.append(_assistant_with_tool_calls(resp, calls))

        for call in calls:
            tool_name = call["name"]
            tool_args = call["arguments"]
            log.info("   🔧 → %s(%s)", tool_name, json.dumps(tool_args, ensure_ascii=False)[:80])

            tool = registry.get(tool_name)
            if not tool:
                content = f"Outil inconnu: {tool_name}"
                log.warning("   ❌ %s", content)
            else:
                # Permission check
                if tool.permission > ToolPermission.READ and ctx.get("read_only"):
                    content = f"Outil en écriture bloqué (mode lecture seule): {tool_name}"
                    log.warning("   🔒 %s", content)
                else:
                    result = await tool.execute(tool_args, ctx)
                    content = result.to_tool_message()
                    if result.ok:
                        log.info("   ✅ %s terminé en %.0fms", tool_name, result.execution_time_ms)
                    else:
                        log.warning("   ❌ %s erreur: %s", tool_name, result.error[:80])

            messages.append({"role": "tool", "tool_call_id": call["id"], "content": content})

        messages = truncate_messages(messages)

    log.warning("   ⚠️  Tool Loop plafonné à %s steps", max_steps)
    last = messages[-1]
    return last.get("content") or "Boucle d'outils plafonnée (max_steps atteint)."
