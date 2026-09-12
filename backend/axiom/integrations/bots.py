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
