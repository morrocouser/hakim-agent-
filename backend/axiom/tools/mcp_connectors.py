"""MCP Connectors Manager pour HakimAgent / AXIOM.

Fournit une interface unifiée pour charger, connecter et gérer les serveurs MCP
configurés (memory, filesystem, puppeteer, github, sqlite, etc.).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from axiom.tools.mcp_bridge import MCPConnectionManager, MCPServerConnection

logger = logging.getLogger(__name__)

# Emplacements prioritaires du fichier de configuration MCP
CONFIG_SEARCH_PATHS = [
    Path("backend/mcp_servers.json"),
    Path("mcp_servers.json"),
    Path("mcp_config.json"),
    Path(os.path.expanduser("~")) / ".gemini" / "config" / "mcp_config.json",
]


class MCPConnectorRegistry:
    """Gestionnaire de connecteurs MCP pour l'écosystème HakimAgent."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._resolve_config_path()
        self.manager = MCPConnectionManager()
        self._configs: Dict[str, dict] = {}
        self._load_config()

    def _resolve_config_path(self) -> Optional[Path]:
        for p in CONFIG_SEARCH_PATHS:
            if p.exists():
                return p
        return None

    def _load_config(self) -> None:
        if not self.config_path or not self.config_path.exists():
            logger.warning("Aucun fichier de configuration MCP détecté.")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._configs = data.get("mcpServers", {})
            logger.info(f"Chargé {len(self._configs)} connecteurs MCP depuis {self.config_path}")
        except Exception as e:
            logger.error(f"Erreur de lecture du fichier MCP {self.config_path}: {e}")

    @property
    def available_connectors(self) -> List[str]:
        """Retourne la liste des connecteurs définis dans la configuration."""
        return list(self._configs.keys())

    @property
    def active_connectors(self) -> List[str]:
        """Retourne la liste des connecteurs actuellement connectés."""
        return self.manager.connected_servers

    async def connect_server(self, name: str, auto_register: bool = True) -> Optional[MCPServerConnection]:
        """Connecte un serveur MCP spécifique par son nom."""
        if name not in self._configs:
            logger.error(f"Serveur MCP '{name}' introuvable dans la configuration.")
            return None

        cfg = self._configs[name]
        command_list = [cfg["command"]] + cfg.get("args", [])
        env = cfg.get("env", {})

        try:
            logger.info(f"Connexion au serveur MCP '{name}' ({command_list[0]})...")
            conn = await self.manager.connect(
                name=name,
                command=command_list,
                env=env,
                auto_register=auto_register,
            )
            logger.info(f"Serveur MCP '{name}' connecté avec succès ({conn.tool_count} outils).")
            return conn
        except Exception as e:
            logger.error(f"Échec de connexion au serveur MCP '{name}': {e}")
            return None

    async def connect_all(self, auto_register: bool = True) -> Dict[str, bool]:
        """Connecte l'ensemble des serveurs configurés."""
        results = {}
        for name in self._configs:
            conn = await self.connect_server(name, auto_register=auto_register)
            results[name] = conn is not None
        return results

    async def disconnect_server(self, name: str) -> None:
        """Déconnecte un serveur MCP."""
        await self.manager.disconnect(name)

    async def close(self) -> None:
        """Ferme toutes les connexions MCP actives."""
        await self.manager.close()

    def get_status(self) -> Dict[str, Any]:
        """Retourne un résumé de l'état des connecteurs."""
        status = {}
        for name, cfg in self._configs.items():
            conn = self.manager.get(name)
            status[name] = {
                "configured": True,
                "connected": conn is not None,
                "tool_count": conn.tool_count if conn else 0,
                "command": cfg.get("command"),
            }
        return status


# Instance singleton globale
_global_connector_registry: Optional[MCPConnectorRegistry] = None


def get_connector_registry() -> MCPConnectorRegistry:
    """Retourne l'instance globale du registre de connecteurs MCP."""
    global _global_connector_registry
    if _global_connector_registry is None:
        _global_connector_registry = MCPConnectorRegistry()
    return _global_connector_registry
