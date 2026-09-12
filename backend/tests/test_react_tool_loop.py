"""Test d'intégration ReActLoop ↔ tool_loop (flag AXIOM_TOOL_LOOP)."""
import asyncio, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from axiom.core.react_loop import ReActLoop
from axiom.core.memory import MemoryManager
from axiom.core.scoring import score_and_route


class FakeClaude:
    def __init__(self, script):
        self.script = list(script)
        self.uses_tools = False
        self.chat_calls = 0

    async def chat(self, model, system, messages, max_tokens=4096):
        self.chat_calls += 1
        return "[repli sans outils]"

    async def chat_with_tools(self, model, system, messages, tools=None, max_tokens=4096):
        self.uses_tools = True
        return self.script.pop(0)


async def test_flag_off():
    os.environ["AXIOM_TOOL_LOOP"] = "0"
    claude = FakeClaude([])
    loop = ReActLoop(MemoryManager(), claude)
    assert loop.tool_loop_enabled is False
    task = score_and_route("écris un hello world")
    res = await loop.execute(task, None)
    assert claude.uses_tools is False
    assert claude.chat_calls >= 1
    assert res.error is None


async def test_flag_on():
    os.environ["AXIOM_TOOL_LOOP"] = "1"
    claude = FakeClaude([{"content": "", "tool_calls": [], "error": None}])
    loop = ReActLoop(MemoryManager(), claude)
    assert loop.tool_loop_enabled is True
    task = score_and_route("écris un hello world")
    res = await loop.execute(task, None)
    assert claude.uses_tools is True
    assert res.error is None


def main():
    asyncio.run(test_flag_off())
    asyncio.run(test_flag_on())
    print("ALL PASS")


if __name__ == "__main__":
    main()