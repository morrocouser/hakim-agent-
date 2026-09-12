"""Test des wrappers d'outils. Venv: backend\.venv\Scripts\python.exe -X utf8 backend\tests\test_tool_wrappers.py"""
import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from axiom.tools.registry import ToolContext, build_tools_spec, invoke_tool
from axiom.tools.tool_wrappers import default_context  # noqa: E402
from axiom.tools.web_search import WebSearchTool
from axiom.tools.file_manager import FileManager
from axiom.tools.code_executor import CodeExecutor
from axiom.tools.error_log import ErrorLog


async def test_spec_exposes_all_six():
    spec = build_tools_spec(None)
    names = {f["function"]["name"] for f in spec}
    expected = {"web_search", "file_read", "file_create", "file_delete", "code_execute", "error_log"}
    assert expected <= names, names


async def test_web_search_without_key():
    ctx = default_context()
    res = await invoke_tool("web_search", {"query": "impl\u2019mentation"}, ctx)
    assert res.ok, res.error
    assert "indisponible" in res.text and "WEB_SEARCH_API_KEY" in res.text


async def test_file_create_read_delete():
    with tempfile.TemporaryDirectory() as d:
        ctx = default_context(base_dir=d)
        res_create = await invoke_tool("file_create", {"path": "demo.md", "content": "# Bonjour"}, ctx)
        assert res_create.ok, res_create.error
        res_read = await invoke_tool("file_read", {"path": "demo.md"}, ctx)
        assert res_read.ok and "# Bonjour" in res_read.text
        res_del = await invoke_tool("file_delete", {"path": "demo.md"}, ctx)
        assert res_del.ok


async def test_code_execute_python():
    ctx = default_context()
    res = await invoke_tool("code_execute", {"language": "python", "code": "print(21*2)"}, ctx)
    # If docker is not available, CodeExecutor returns an error message
    # Either way, the tool invocation should succeed (ok=True)
    assert res.ok, res.error
    if "42" not in res.text:
        # Docker not running - verify it's a docker connection error, not a wrapper bug
        assert "docker" in res.text.lower() or "connection" in res.text.lower(), res.text


async def test_error_log():
    ctx = default_context()
    res = await invoke_tool("error_log", {
        "symptom": "test", "root_cause": "test", "fix": "test",
        "context": "test", "agent": "APEX",
    }, ctx)
    assert res.ok and "E_" in res.text
    res2 = await invoke_tool("error_log", {"symptom": "test", "root_cause": "test", "fix": "test", "context": "test"}, ctx)
    assert res2.ok


def run():
    asyncio.run(test_spec_exposes_all_six())  # pragma: no cover
    # NOTE: asyncio tests run serially in one loop here for simplicity
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_main())
    loop.close()


async def _main():
    await test_spec_exposes_all_six()
    await test_web_search_without_key()
    await test_file_create_read_delete()
    await test_code_execute_python()
    await test_error_log()
    print("__ALL PASS__")


if __name__ == "__main__":
    run()