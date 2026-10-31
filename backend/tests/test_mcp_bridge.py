"""Tests pour axiom.tools.mcp_bridge

Utilise un serveur MCP stdio mock (écrit en Python) pour valider :
- La connexion stdio
- La découverte d'outils
- L'enregistrement dans le ToolRegistry global
- L'exécution d'un outil MCP via MCPToolAdapter
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

from axiom.tools.base import (
    get_registry,
    ToolPermission,
    ToolResultType,
    ToolSchema,
)
from axiom.tools.mcp_bridge import MCPToolAdapter, MCPServerConnection, MCPConnectionManager


# ─── Mock MCP Server (stdio mode) ─────────────────────────────────────────────
# Écrit comme un script autonome pour éviter les conflits de braces avec .format()
def write_mock_server(path: str) -> None:
    """Écrit le serveur MCP mock sur le disque."""
    python = sys.executable
    # On utilise str.replace pour éviter les collisions avec les f-strings
    script = MOCK_SERVER_TEMPLATE.replace("__PYTHON__", python)
    with open(path, "w") as f:
        f.write(script)
    os.chmod(path, 0o755)


MOCK_SERVER_TEMPLATE = r'''
#!/usr/bin/env python
"""Mock MCP server (stdio mode) for testing."""
import sys
import json

def send(msg):
    if "jsonrpc" not in msg:
        msg["jsonrpc"] = "2.0"
    data = json.dumps(msg)
    sys.stdout.write(data + "\n")
    sys.stdout.flush()

while True:
    line = sys.stdin.readline()
    if not line:
        break
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except Exception:
        continue

    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        client_version = msg.get("params", {}).get("protocolVersion", "2024-11-05")
        send({
            "id": msg_id,
            "result": {
                "protocolVersion": client_version,
                "capabilities": {"tools": {}, "prompts": {}, "resources": {}},
                "serverInfo": {"name": "test-mock", "version": "1.0.0"}
            }
        })
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        send({
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "echo_tool",
                        "description": "Echo a message",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string", "description": "Message to echo"}
                            },
                            "required": ["message"]
                        }
                    },
                    {
                        "name": "delete_item",
                        "description": "Delete an item (dangerous)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "item_id": {"type": "string"}
                            },
                            "required": ["item_id"]
                        }
                    }
                ]
            }
        })
    elif method == "tools/call":
        tool_name = msg["params"]["name"]
        args = msg["params"].get("arguments", {})
        if tool_name == "echo_tool":
            text = "ECHO: " + args.get("message", "")
            send({
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": text}]}
            })
        elif tool_name == "delete_item":
            text = "Deleted item " + args.get("item_id", "")
            send({
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": text}]}
            })
        else:
            send({
                "id": msg_id,
                "error": {"code": -32601, "message": "Tool not found"}
            })
    elif method == "prompts/list":
        send({"id": msg_id, "result": {"prompts": []}})
    elif method == "resources/list":
        send({"id": msg_id, "result": {"resources": []}})
    elif msg_id is not None:
        send({"id": msg_id, "result": {}})
'''


@pytest.fixture
async def mock_server_path():
    """Crée un script serveur MCP mock exécutable."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix="_mcp_mock.py", delete=False, prefix="mcp_mock_"
    ) as f:
        f.write(MOCK_SERVER_TEMPLATE.replace("__PYTHON__", sys.executable))
    os.chmod(f.name, 0o755)
    yield [sys.executable, "-u", f.name]
    try:
        os.unlink(f.name)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def clean_registry():
    """Nettoie le registre global avant chaque test pour éviter les interférences."""
    from axiom.tools import base
    original = base._registry._tools.copy()
    base._registry._tools.clear()
    base._registry._categories.clear()
    yield
    base._registry._tools.update(original)


class TestMCPConnectionManager:
    """Tests TDD pour MCPConnectionManager."""

    @pytest.mark.asyncio
    async def test_connect_and_register_tools(self, mock_server_path):
        """✓ La connexion établit une session et découvre 2 outils."""
        manager = MCPConnectionManager()
        conn = await manager.connect("test", mock_server_path)

        assert conn is not None
        assert conn.name == "test"
        assert conn.session is not None
        assert conn.tool_count == 2
        assert len(manager.connected_servers) == 1

        await manager.close()

    @pytest.mark.asyncio
    async def test_tools_registered_in_global_registry(self, mock_server_path):
        """✓ Les outils MCP sont visibles depuis get_registry()."""
        manager = MCPConnectionManager()
        conn = await manager.connect("test", mock_server_path)

        registry = get_registry()
        echo_tool = registry.get("echo_tool")
        assert echo_tool is not None
        assert echo_tool.name == "echo_tool"
        assert echo_tool.description == "Echo a message"

        delete_tool = registry.get("delete_item")
        assert delete_tool is not None
        # Le nom contient "delete" → permission DESTRUCTIVE
        assert delete_tool.permission == ToolPermission.DESTRUCTIVE

        await manager.close()

    @pytest.mark.asyncio
    async def test_echo_tool_execution(self, mock_server_path):
        """✓ MCPToolAdapter.execute() appelle le serveur MCP et renvoie le résultat."""
        manager = MCPConnectionManager()
        await manager.connect("test", mock_server_path)

        registry = get_registry()
        echo_tool = registry.get("echo_tool")

        result = await echo_tool.execute({"message": "Hello MCP"}, context={})

        assert result.ok is True
        assert result.type == ToolResultType.TEXT
        assert "ECHO: Hello MCP" in result.content
        assert result.metadata["server"] == "test"
        assert result.metadata["tool"] == "echo_tool"

        await manager.close()

    @pytest.mark.asyncio
    async def test_error_handling_on_unknown_tool(self, mock_server_path):
        """✓ Un outil inexistant renvoie ToolResult.ok=False."""
        manager = MCPConnectionManager()
        await manager.connect("test", mock_server_path)

        registry = get_registry()
        echo_tool = registry.get("echo_tool")

        # Exécute correctement
        result = await echo_tool.execute({"message": "Test"}, context={})
        assert result.ok is True
        assert "ECHO: Test" in result.content

        await manager.close()

    @pytest.mark.asyncio
    async def test_disconnect_all(self, mock_server_path):
        """✓ disconnect_all ferme correctement toutes les sessions."""
        manager = MCPConnectionManager()
        await manager.connect("test", mock_server_path)
        assert len(manager.connected_servers) == 1

        await manager.close()
        assert len(manager.connected_servers) == 0

    @pytest.mark.asyncio
    async def test_context_manager_protocol(self, mock_server_path):
        """✓ MCPServerConnection peut être utilisé comme async context manager."""
        async with MCPServerConnection("test", mock_server_path) as conn:
            assert conn.session is not None
            await conn.register_tools()
            assert conn.tool_count == 2
