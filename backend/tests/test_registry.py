"""Tests du registre central d'outils de APEX. Exécuter avec le venv :
backend\.venv\Scripts\python.exe -X utf8 backend\tests\test_registry.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel, Field
from axiom.tools.registry import (  # noqa: E402
    ToolContext, ToolResult, axiom_tool, build_tools_spec, get_tools, invoke_tool,
)


@axiom_tool("demo_echo", "Description demo", schema=None)
def _echo(params, ctx: ToolContext) -> str:
    return f"ech\xc3\xa9:{params}"


class PingParams(BaseModel):
    message: str = Field(..., description="Message \u00e0 renvoyer")


@axiom_tool("demo_ping2", "Ping de test", schema=PingParams, permissions="write")
def _ping(params: PingParams, ctx: ToolContext) -> str:
    return f"pong {params.message}"


async def test_decorator_registers():
    names = [t["name"] for t in get_tools()]
    assert "demo_echo" in names, names
    assert "demo_ping2" in names, names


async def test_invoke_sync_and_schema():
    spec = build_tools_spec(ToolContext())
    by_name = {f["function"]["name"]: f["function"] for f in spec}
    ping = by_name.get("demo_ping2")
    assert ping, "demo_ping2 absent de build_tools_spec"
    assert ping["description"] == "Ping de test"
    assert "message" in ping["parameters"]["properties"]
    ok = await invoke_tool("demo_ping2", {"message": "coucou"}, ToolContext())
    assert ok.ok and ok.text == "pong coucou"


async def test_unknown_tool():
    res = await invoke_tool("outil_inconnu", {})
    assert not res.ok and "inconnu" in res.error


async def test_read_only_blocks_write():
    res = await invoke_tool("demo_ping2", {"message": "x"}, ToolContext(read_only=True))
    assert not res.ok and "lecture seule" in res.error


async def test_missing_schema_params():
    res = await invoke_tool("demo_ping2", {}, ToolContext())
    assert not res.ok, res


async def main():
    await test_decorator_registers()
    await test_invoke_sync_and_schema()
    await test_unknown_tool()
    await test_read_only_blocks_write()
    await test_missing_schema_params()
    print("ALL PASS")


if __name__ == "__main__":
    asyncio.run(main())