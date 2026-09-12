from __future__ import annotations

import json
from typing import Optional

from axiom.tools.registry import ToolContext, build_tools_spec, invoke_tool

DEFAULT_MAX_STEPS = 5
MAX_MESSAGES = 24


def truncate_messages(messages: list[dict]) -> list[dict]:
    """Garder le premier message utilisateur + les derniers MAX_MESSAGES."""
    if len(messages) <= MAX_MESSAGES:
        return messages
    head = [m for m in messages if m.get("role") == "user"][:1]
    tail = messages[1:]
    limit = MAX_MESSAGES - len(head)
    return head + tail[-limit:]


# Flag pour activer/désactiver le tool loop
HAKIM_TOOL_LOOP = True  # par défaut activé


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


async def run_tool_loop(
    claude,
    model: str,
    system: str,
    user_prompt: str,
    ctx: Optional[ToolContext] = None,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> str:
    """Boucle interne de function calling. Retourne le texte final.

    Si aucune tool n'est exposée (spec vide) ou si le provider refuse le
    function calling (erreur), on replie sur un appel `chat()` simple.
    """
    ctx = ctx or ToolContext()
    tools = build_tools_spec(ctx)
    messages = [{"role": "user", "content": user_prompt}]

    if not tools or not HAKIM_TOOL_LOOP:
        return await claude.chat(model=model, system=system, messages=messages)

    for _ in range(max_steps):
        resp = await claude.chat_with_tools(
            model=model, system=system, messages=messages, tools=tools,
        )
        if resp.get("error"):
            # Repli : provider refuse/dysfonctionne → chat simple sans tools
            return await claude.chat(model=model, system=system, messages=messages)

        calls = resp.get("tool_calls") or []
        if not calls:
            return resp.get("content") or ""

        messages.append(_assistant_with_tool_calls(resp, calls))
        for call in calls:
            result = await invoke_tool(call["name"], call["arguments"], ctx)
            if result.ok:
                content = result.text
            else:
                content = f"[Tool {call['name']} error] {result.error}"
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": content})
        messages = truncate_messages(messages)

    # Plafond de steps atteint : retour du dernier contenu assistant produit
    last = messages[-1]
    return last.get("content") or "Boucle d'outils plafonnée (max_steps atteint)."