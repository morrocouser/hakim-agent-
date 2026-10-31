"""Telegram & Discord Bot Integrations — Remote Control & Notifications.

Allows remote control of the AXIOM / Antigravity agent via Telegram and Discord.
"""

from __future__ import annotations

import os
import json
import asyncio
import urllib.request
import urllib.parse
from typing import Optional
from axiom.logging_setup import log


class TelegramBotService:
    """Service d'intégration Telegram Bot."""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    async def send_notification(self, text: str) -> bool:
        """Envoie un message de notification vers Telegram."""
        if not self.is_configured():
            log.info("   📱 Telegram Bot non configuré (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID manquant)")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: urllib.request.urlopen(req))
            log.info("   📱 Notification Telegram envoyée avec succès !")
            return True
        except Exception as e:
            log.error("   ❌ Erreur d'envoi Telegram: %s", e)
            return False


class DiscordWebhookService:
    """Service d'intégration Discord Webhook."""

    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def send_notification(self, title: str, description: str, color: int = 65280) -> bool:
        """Envoie une notification sous forme d'Embed vers Discord."""
        if not self.is_configured():
            log.info("   💬 Discord Webhook non configuré (DISCORD_WEBHOOK_URL manquant)")
            return False

        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": description,
                    "color": color,
                    "footer": {"text": "Google Antigravity 2.0 / AXIOM Bot"},
                }
            ]
        }
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: urllib.request.urlopen(req))
            log.info("   💬 Notification Discord envoyée avec succès !")
            return True
        except Exception as e:
            log.error("   ❌ Erreur d'envoi Discord: %s", e)
            return False


# ─── Tool Adapters for Agent Tool Registry ───────────────────────────────────

from axiom.tools.base import (
    BaseTool, ToolResult, ToolResultType, ToolPermission, ToolSchema
)


class TelegramTool(BaseTool):
    """Outil d'envoi de messages via Telegram."""

    _name = "telegram_notify"
    _description = "Envoie des alertes et messages vers Telegram via bot_token et chat_id."
    _permission = ToolPermission.WRITE

    def __init__(self, base_dir: str = "."):
        self._service = TelegramBotService()
        self._schema = ToolSchema(
            name=self._name,
            description=self._description,
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Texte du message à envoyer sur Telegram",
                    }
                },
                "required": ["message"],
            },
            required=["message"],
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        msg = params.get("message", "")
        if not msg:
            return ToolResult(ok=False, error="Le paramètre 'message' est requis", type=ToolResultType.ERROR)

        if self._service.is_configured():
            ok = await self._service.send_notification(msg)
            if ok:
                return ToolResult(
                    ok=True,
                    content=f"[Telegram Live] Message transmis avec succès sur le chat {self._service.chat_id} !",
                    type=ToolResultType.TEXT,
                )
            else:
                return ToolResult(
                    ok=False,
                    error="Échec d'envoi vers l'API Telegram. Vérifiez votre bot_token.",
                    type=ToolResultType.ERROR,
                )

        return ToolResult(
            ok=True,
            content=(
                f"[Telegram Preview] Message préparé : '{msg}'\n"
                f"💡 Pour envoyer de réelles notifications Telegram, configurez "
                f"TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID dans backend/.env."
            ),
            type=ToolResultType.TEXT,
            metadata={"live": False},
        )


class DiscordTool(BaseTool):
    """Outil d'envoi de messages via Discord Webhook."""

    _name = "discord_notify"
    _description = "Envoie des alertes riches (embeds) vers un salon Discord via un webhook."
    _permission = ToolPermission.WRITE

    def __init__(self, base_dir: str = "."):
        self._service = DiscordWebhookService()
        self._schema = ToolSchema(
            name=self._name,
            description=self._description,
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Titre de la notification Discord",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description ou corps du message Discord",
                    },
                },
                "required": ["title", "description"],
            },
            required=["title", "description"],
        )

    async def _execute(self, params: dict, context: dict) -> ToolResult:
        title = params.get("title", "")
        desc = params.get("description", "")
        if not title or not desc:
            return ToolResult(ok=False, error="Paramètres 'title' et 'description' requis", type=ToolResultType.ERROR)

        if self._service.is_configured():
            ok = await self._service.send_notification(title, desc)
            if ok:
                return ToolResult(
                    ok=True,
                    content=f"[Discord Live] Notification '{title}' envoyée avec succès sur le salon Discord !",
                    type=ToolResultType.TEXT,
                )
            else:
                return ToolResult(
                    ok=False,
                    error="Échec d'envoi Discord. Vérifiez votre DISCORD_WEBHOOK_URL.",
                    type=ToolResultType.ERROR,
                )

        return ToolResult(
            ok=True,
            content=(
                f"[Discord Preview] Notification préparée : '{title}' - '{desc}'\n"
                f"💡 Pour envoyer de réelles alertes Discord, configurez "
                f"DISCORD_WEBHOOK_URL dans backend/.env."
            ),
            type=ToolResultType.TEXT,
            metadata={"live": False},
        )
