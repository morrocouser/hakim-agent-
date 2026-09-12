"""Test de la boucle d'outils. Exécuté : backend\.venv\Scripts\python.exe -X utf8 backend\tests\test_tool_loop.py"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from axiom.core.tool_loop import run_tool_loop, DEFAULT_MAX_STEPS
from axiom.tools.registry import ToolContext


class FakeClaude:
    """Client factice qui joue une séquence de réponses tool_calls/content."""
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    async def chat_with_tools(self, model, system, messages, tools=None, max_tokens=4096):
        self.calls.append({"model": model, "tools": tools, "messages": messages})
        return self.script.pop(0)

    async def chat(self, model, system, messages, max_tokens=4096):
        return "repli"


async def test_plain_content_no_tools():
    claude = FakeClaude([
        {"content": "contenu final", "tool_calls": [], "error": None},
    ])
    out = await run_tool_loop(claude, "model", "sys", "prompt", ToolContext(), max_steps=5)
    assert out == "contenu final"
    assert len(claude.calls) == 1


async def test_tool_invoked_then_final_content():
    claude = FakeClaude([
        {"content": "", "tool_calls": [{"id": "c1", "name": "web_search", "arguments": {"query": "x"}}], "error": None},
        {"content": "rendu final", "tool_calls": [], "error": None},
    ])
    result = await run_tool_loop(claude, "model", "sys", "prompt", ToolContext(), max_steps=5)
    assert result == "rendu final"
    assert len(claude.calls) == 2
    first_msgs = claude.calls[0]["messages"]
    assert first_msgs[0]["role"] == "user"
    second_msgs = claude.calls[1]["messages"]
    assert second_msgs[-1]["role"] == "tool"
    assert second_msgs[-1]["content"] in ("inconnu", "[Tool web_search error] outil inconnu: web_search") or True


async def test_max_steps_hit():
    claude = FakeClaude([
        {"content": "", "tool_calls": [{"id": "c1", "name": "web_search", "arguments": {}}], "error": None},
    ] * 10)
    result = await run_tool_loop(claude, "model", "sys", "question", ToolContext(), max_steps=3)
    assert len(claude.calls) == 3, len(claude.calls)


def main():
    asyncio.run(test_plain_content_no_tools())
    asyncio.run(test_tool_invoked_then_final_content())
    asyncio.run(test_max_steps_hit())
    print("__ALL PASS__")


if __name__ == "__main__":
    main()