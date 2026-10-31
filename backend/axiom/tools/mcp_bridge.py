"""MCP Bridge — Connecte des serveurs MCP (stdio) au registre d'outils AXIOM.

Permet à HakimAgent de découvrir et utiliser dynamiquement des outils provenant
de n'importe quel serveur MCP tiers (GitHub, PostgreSQL, système de fichiers, etc.)
sans écrire de wrappers Python spécifiques.

Usage:
    from axiom.tools.mcp_bridge import MCPConnectionManager

    manager = MCPConnectionManager()
    conn = await manager.connect("filesystem", [sys.executable, "-m", "mcp_server_filesystem"])
    await conn.register_tools()  # outils MCP disponibles dans le ToolRegistry global
    await manager.close()
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from typing import Optional

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

from axiom.tools.base import (
    BaseTool,
    ToolResult,
    ToolResultType,
    ToolSchema,
    ToolPermission,
    get_registry,
)

logger = logging.getLogger(__name__)


class MCPToolAdapter(BaseTool):
    """Adapte un outil MCP au protocole Tool d'AXIOM.

    Chaque outil exposé par un serveur MCP est encapsulé dans cette classe
    qui implémente `BaseTool`. L'exécution est déléguée via `session.call_tool`.
    """

    def __init__(self, mcp_tool_info, connection: "MCPServerConnection", server_name: str):
        self._name = mcp_tool_info.name
        self._description = mcp_tool_info.description or ""
        self._connection = connection  # stocke la connexion pour accéder à la session
        self._server_name = server_name
        self._params = mcp_tool_info

        # Permission par défaut : READ (peut être surchargée via le nom)
        # Convention : si le nom contient "delete"/"drop"/"remove" -> DESTRUCTIVE
        lower_name = mcp_tool_info.name.lower()
        if any(k in lower_name for k in ("delete", "drop", "remove", "destroy")):
            self._permission = ToolPermission.DESTRUCTIVE
        elif any(k in lower_name for k in ("write", "create", "edit", "update", "save")):
            self._permission = ToolPermission.WRITE
        else:
            self._permission = ToolPermission.READ

        # Schéma JSON Schema depuis le serveur MCP (compatible SDK snake_case et camelCase)
        input_schema = (
            getattr(mcp_tool_info, "input_schema", None)
            or getattr(mcp_tool_info, "inputSchema", None)
            or {
                "type": "object",
                "properties": {},
            }
        )
        self._schema = ToolSchema(
            name=mcp_tool_info.name,
            description=mcp_tool_info.description or "",
            parameters=input_schema,
            required=input_schema.get("required", []),
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        try:
            session = self._connection.session
            if session is None:
                return ToolResult(
                    ok=False,
                    error=f"[{self._name}] Session MCP non disponible",
                    type=ToolResultType.ERROR,
                )

            res = await session.call_tool(self._name, arguments=params)
            # Les réponses MCP sont des listes de contenus (text, image, etc.)
            content_parts = []
            for item in res.content:
                if hasattr(item, "text") and item.text:
                    content_parts.append(item.text)
                elif hasattr(item, "type") and getattr(item, "type", "") == "image":
                    content_parts.append(f"[image:{item.type}]")
                else:
                    content_parts.append(str(item))

            return ToolResult(
                ok=True,
                content="\n".join(content_parts),
                type=ToolResultType.TEXT,
                metadata={
                    "server": self._server_name,
                    "tool": self._name,
                },
            )
        except Exception as e:
            return ToolResult(
                ok=False,
                error=f"[{self._name}] MCP error: {e}",
                type=ToolResultType.ERROR,
            )


class MCPServerConnection:
    """Gère une session MCP stdio active et les outils associés.

    Cycle de vie : connect → register_tools → execute → disconnect.

    Note Windows : `stdio_client` nécessite un `errlog` avec `fileno()` valide.
    Sur Windows, on utilise un fichier temporaire pour stderr comme fallback.
    """

    def __init__(self, name: str, command: list[str], env: Optional[dict] = None):
        self.name = name
        self.command = command
        self.env = env or {}
        self._session: Optional[ClientSession] = None
        self._server_info: Optional[dict] = None
        self._tool_adapters: list[MCPToolAdapter] = []
        self._stdio_ctx = None
        self._session_ctx = None
        self._errlog = None
        self._read_stream = None
        self._write_stream = None

    async def __aenter__(self) -> "MCPServerConnection":
        await self.connect()
        return self

    async def __aexit__(self, *exc):
        await self.disconnect()

    async def connect(self) -> ClientSession:
        """Établit la connexion stdio et initialise la session MCP."""
        server_params = StdioServerParameters(
            command=self.command[0],
            args=self.command[1:],
            env={**os.environ, **self.env},
        )

        # Sur Windows, errlog=sys.stderr peut échouer si stderr n'a pas de fileno.
        errlog = _get_safe_errlog()
        self._errlog = errlog

        # stdio_client est un @asynccontextmanager — utiliser async with
        self._stdio_ctx = stdio_client(server_params, errlog=errlog)
        # On stocke le context manager pour le fermer proprement plus tard
        self._read_stream, self._write_stream = await self._stdio_ctx.__aenter__()

        self._session_ctx = ClientSession(self._read_stream, self._write_stream)
        self._session = await self._session_ctx.__aenter__()

        # Initialise la session (negocie les capabilities)
        result = await self._session.initialize()
        self._server_info = result.model_dump() if result else {}

        info = self._server_info.get("serverInfo", {}) or {}
        logger.info(
            f"MCP connecté à '{self.name}': "
            f"{info.get('name', '?')} v{info.get('version', '?')}"
        )
        return self._session

    async def register_tools(self) -> list[MCPToolAdapter]:
        """Découvre tous les outils du serveur et les enregistre dans le registre global."""
        if self._session is None:
            raise RuntimeError(
                f"MCPServerConnection '{self.name}' non connectée. Appelez .connect() d'abord."
            )

        tools_resp = await self._session.list_tools()
        registry = get_registry()

        for tool_info in tools_resp.tools:
            adapter = MCPToolAdapter(tool_info, self, self.name)
            # Éviter les doublons
            if registry.get(tool_info.name) is None:
                registry.register(adapter, f"mcp:{self.name}")
            self._tool_adapters.append(adapter)
            logger.debug(
                f"Outil MCP enregistré: {tool_info.name} (serveur: {self.name})"
            )

        return self._tool_adapters

    async def disconnect(self) -> None:
        """Déconnecte proprement la session MCP.

        Utilise un timeout de 5 secondes pour le teardown du ClientSession,
        car le MCP SDK peut rester bloqué sur la fermeture des pipes stdio
        (notamment sous Windows). Le process serveur est tué en dernier ressort.
        """
        import anyio

        # Fermeture de la session ClientSession (avec timeout)
        if self._session_ctx is not None:
            try:
                with anyio.move_on_after(5.0):
                    await self._session_ctx.__aexit__(None, None, None)
            except Exception:
                pass
        # Fermeture du stdio_client (processus serveur)
        if self._stdio_ctx is not None:
            try:
                with anyio.move_on_after(5.0):
                    await self._stdio_ctx.__aexit__(None, None, None)
            except Exception:
                pass
        # Fermeture du errlog temporaire (ne jamais fermer sys.stderr ou sys.stdout)
        if self._errlog is not None and self._errlog not in (sys.stderr, sys.stdout):
            try:
                if hasattr(self._errlog, "close"):
                    self._errlog.close()
            except Exception:
                pass
        # Nettoyage
        self._session = None
        self._server_info = None
        self._session_ctx = None
        self._stdio_ctx = None
        self._errlog = None
        self._read_stream = None
        self._write_stream = None

    @property
    def session(self) -> Optional[ClientSession]:
        return self._session

    @property
    def tool_count(self) -> int:
        return len(self._tool_adapters)


class MCPConnectionManager:
    """Gestionnaire de connexions MCP — registre des serveurs configurés.

    Usage:
        manager = MCPConnectionManager()
        server = await manager.connect("github", [sys.executable, "-m", "mcp_server_github"])
    """

    def __init__(self):
        self._connections: dict[str, MCPServerConnection] = {}

    async def connect(
        self,
        name: str,
        command: list[str],
        env: Optional[dict] = None,
        auto_register: bool = True,
    ) -> MCPServerConnection:
        """Connecte à un serveur MCP stdio et (optionnellement) enregistre ses outils.

        Args:
            name: Identifiant unique du serveur MCP.
            command: Commande d'exécution (ex: ["python", "-m", "mcp_server_filesystem"]).
            env: Variables d'environnement supplémentaires.
            auto_register: Si True, découvre et enregistre les outils automatiquement.

        Returns:
            MCPServerConnection active.
        """
        # Ferme une connexion existante avec le même nom
        if name in self._connections:
            await self._connections[name].disconnect()

        conn = MCPServerConnection(name, command, env)
        await conn.connect()

        if auto_register:
            await conn.register_tools()

        self._connections[name] = conn
        return conn

    async def disconnect(self, name: str) -> None:
        """Déconnecte un serveur MCP par son nom."""
        if name in self._connections:
            await self._connections[name].disconnect()
            del self._connections[name]

    async def disconnect_all(self) -> None:
        """Déconnecte tous les serveurs MCP."""
        for name in list(self._connections.keys()):
            await self.disconnect(name)

    def get(self, name: str) -> Optional[MCPServerConnection]:
        """Récupère une connexion par son nom."""
        return self._connections.get(name)

    @property
    def connected_servers(self) -> list[str]:
        """Liste des noms de serveurs connectés."""
        return list(self._connections.keys())

    async def close(self) -> None:
        """Alias pour disconnect_all — compatibilité lifecycle."""
        await self.disconnect_all()


def _get_safe_errlog():
    """Retourne un errlog fiable pour stdio_client.

    Sur Windows, sys.stderr peut ne pas avoir de fileno valide quand le
    processus est lancé depuis un environnement restreint (ex: execute_code).
    On utilise un fichier temporaire comme fallback sûr.
    """
    try:
        sys.stderr.fileno()
        return sys.stderr
    except (OSError, ValueError, AttributeError):
        # Fallback : fichier temporaire
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix="_mcp_err.log", prefix="mcp_", delete=False
        )
        tmp_path = tmp.name
        import atexit
        atexit.register(
            lambda: os.unlink(tmp_path) if os.path.exists(tmp_path) else None
        )
        return tmp
