"""
HakimAgent - Tests d'Intégration Réelle du Protocole MCP (Model Context Protocol) (Étape 7)
Valide :
1. Le chargement et la structure des connecteurs depuis mcp_config.json
2. L'initialisation d'un serveur MCP stdio via MCPServerConnection
3. La découverte dynamique des outils et schémas JSON Schema
4. L'enregistrement automatique dans le ToolRegistry global d'AXIOM
5. La classification de sécurité des permissions (READ vs DESTRUCTIVE)
6. L'exécution d'un appel d'outil (call_tool) et la capture structurée de la réponse
7. La déconnexion propre et la libération des ressources de processus
"""

import sys
import os
import json
import pytest
import asyncio
from pathlib import Path

# Force UTF-8 sous Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from axiom.tools.mcp_connectors import MCPConnectorRegistry
from axiom.tools.mcp_bridge import MCPConnectionManager, MCPServerConnection, MCPToolAdapter
from axiom.tools.base import get_registry, ToolPermission, ToolResultType


@pytest.mark.asyncio
async def test_mcp_connectors_configuration_loading():
    """Vérifie le chargement de la configuration des 13 serveurs MCP déclarés."""
    registry = MCPConnectorRegistry()
    connectors = registry.available_connectors
    assert len(connectors) >= 10, f"Attendu au moins 10 connecteurs MCP, trouvé : {connectors}"
    
    # Vérification des serveurs indispensables
    for expected in ["filesystem", "memory", "sequential-thinking", "github", "rea"]:
        assert expected in connectors, f"Serveur MCP '{expected}' manquant dans la configuration"

    print(f"\n  ✅ Configuration MCP validée : {len(connectors)} serveurs répertoriés ({', '.join(connectors[:5])}...)")


@pytest.mark.asyncio
async def test_mcp_stdio_server_lifecycle_and_tool_execution(tmp_path):
    """
    Lance un serveur MCP stdio réel (mock server local),
    négocie le protocole JSON-RPC, enregistre les outils dans le ToolRegistry
    et exécute un appel d'outil de bout en bout.
    """
    mock_server_script = tmp_path / "mock_mcp_server.py"
    mock_server_script.write_text(r'''
import sys, json

def send(msg):
    if "jsonrpc" not in msg:
        msg["jsonrpc"] = "2.0"
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

while True:
    line = sys.stdin.readline()
    if not line:
        break
    msg = json.loads(line.strip())
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        send({
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "hakim-mcp-test", "version": "1.0.0"}
            }
        })
    elif method == "tools/list":
        send({
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "hakim_echo",
                        "description": "Echo un message de test",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"text": {"type": "string"}},
                            "required": ["text"]
                        }
                    },
                    {
                        "name": "delete_temporary_cache",
                        "description": "Supprime le cache (action destructive)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"cache_id": {"type": "string"}},
                            "required": ["cache_id"]
                        }
                    }
                ]
            }
        })
    elif method == "tools/call":
        params = msg.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        if tool_name == "hakim_echo":
            send({
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": f"ECHO_REPLY: {args.get('text')}"}]
                }
            })
        elif tool_name == "delete_temporary_cache":
            send({
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": f"DELETED: {args.get('cache_id')}"}]
                }
            })
''', encoding="utf-8")

    # 1. Connexion au serveur
    conn = MCPServerConnection(
        name="hakim_test_server",
        command=[sys.executable, str(mock_server_script)],
    )

    await conn.connect()
    assert conn.session is not None, "La session MCP doit être initialisée"

    # 2. Découverte et enregistrement dynamique des outils
    adapters = await conn.register_tools()
    assert len(adapters) == 2
    adapter_names = [a.name for a in adapters]
    assert "hakim_echo" in adapter_names
    assert "delete_temporary_cache" in adapter_names

    # 3. Vérification de la classification automatique des permissions de sécurité
    echo_adapter = next(a for a in adapters if a.name == "hakim_echo")
    delete_adapter = next(a for a in adapters if a.name == "delete_temporary_cache")

    assert echo_adapter.permission == ToolPermission.READ
    assert delete_adapter.permission == ToolPermission.DESTRUCTIVE, "Les outils 'delete_*' doivent être DESTRUCTIVE"

    # 4. Enregistrement dans le ToolRegistry global
    global_registry = get_registry()
    assert global_registry.get("hakim_echo") is not None

    # 5. Exécution d'un appel d'outil réel
    result = await echo_adapter.execute(
        {"text": "Bonjour HakimAgent MCP"},
        context={}
    )

    assert result.ok is True
    assert result.type == ToolResultType.TEXT
    assert "ECHO_REPLY: Bonjour HakimAgent MCP" in result.content

    # 6. Déconnexion propre
    await conn.disconnect()
    assert conn.session is None
    print("  ✅ Cycle de vie complet MCP validé : Connexion -> Découverte -> Permissions -> Exécution -> Déconnexion")


if __name__ == "__main__":
    print("=" * 70)
    print("🔌 TESTS D'INTÉGRATION DU PROTOCOLE MCP (MODEL CONTEXT PROTOCOL)")
    print("=" * 70)
    asyncio.run(test_mcp_connectors_configuration_loading())
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        asyncio.run(test_mcp_stdio_server_lifecycle_and_tool_execution(Path(td)))
    print("=" * 70)
    print("🎉 TOUS LES TESTS MCP SONT VALIDÉS AVEC SUCCÈS !")
    print("=" * 70)
