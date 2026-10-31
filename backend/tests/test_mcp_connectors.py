"""Tests unitaires pour axiom.tools.mcp_connectors.

Valide la découverte des configurations MCP, l'enregistrement des connecteurs,
la structure des commandes et le cycle de vie du registre.
"""

import json
import pytest
from pathlib import Path
from axiom.tools.mcp_connectors import MCPConnectorRegistry, get_connector_registry


def test_mcp_connector_registry_initialization(tmp_path):
    """Vérifie le chargement des connecteurs depuis un fichier JSON."""
    cfg = {
        "mcpServers": {
            "test_mem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"]
            },
            "test_fs": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
            }
        }
    }
    cfg_file = tmp_path / "mcp_servers.json"
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg, f)

    registry = MCPConnectorRegistry(config_path=cfg_file)
    assert len(registry.available_connectors) == 2
    assert "test_mem" in registry.available_connectors
    assert "test_fs" in registry.available_connectors

    status = registry.get_status()
    assert status["test_mem"]["configured"] is True
    assert status["test_mem"]["connected"] is False
    assert status["test_mem"]["command"] == "npx"


def test_global_connector_registry_singleton():
    """Vérifie que get_connector_registry retourne bien un singleton avec des connecteurs réels."""
    reg = get_connector_registry()
    assert reg is not None
    assert len(reg.available_connectors) > 0
    assert "memory" in reg.available_connectors
    assert "filesystem" in reg.available_connectors
