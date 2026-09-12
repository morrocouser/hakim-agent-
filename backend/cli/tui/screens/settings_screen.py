from textual.screen import Screen
from textual.widgets import Static, Input, Button, Select
from textual.containers import Vertical, Horizontal
from cli.tui.config import CONFIG, save_config


class SettingsScreen(Screen):
    """Écran de paramètres."""

    BINDINGS = [
        ("escape", "close", "Fermer"),
    ]

    def compose(self):
        yield Vertical(
            Static("⚙️ PARAMÈTRES", id="settings-title", classes="help-section"),
            Static("API & Modèles", classes="setting-group"),
            Horizontal(
                Static("API Base URL:", classes="setting-label"),
                Input(value=CONFIG.api_base_url, id="api_url", placeholder="http://localhost:8000/api/v1"),
                classes="setting-row",
            ),
            Horizontal(
                Static("OpenRouter Key:", classes="setting-label"),
                Input(value=CONFIG.openrouter_api_key, id="api_key", placeholder="sk-or-v1-...", password=True),
                classes="setting-row",
            ),
            Horizontal(
                Static("Agent par défaut:", classes="setting-label"),
                Select([
                    ("Auto", "auto"),
                    ("Architect", "AGENT_ARCHITECT"),
                    ("Coder", "AGENT_CODER"),
                    ("Debugger", "AGENT_DEBUGGER"),
                    ("Analyst", "AGENT_ANALYST"),
                    ("Writer", "AGENT_WRITER"),
                    ("Researcher", "AGENT_RESEARCHER"),
                    ("Planner", "AGENT_PLANNER"),
                    ("QuickShot", "AGENT_QUICKSHOT"),
                ], value=CONFIG.default_agent or "auto", id="default_agent"),
                classes="setting-row",
            ),
            Static("Interface", classes="setting-group"),
            Horizontal(
                Static("Mode compact:", classes="setting-label"),
                Button("Activé" if CONFIG.compact_mode else "Désactivé", id="compact_toggle", variant="primary" if CONFIG.compact_mode else "default"),
                classes="setting-row",
            ),
            Horizontal(
                Static("Timestamps:", classes="setting-label"),
                Button("Activé" if CONFIG.show_timestamps else "Désactivé", id="timestamp_toggle", variant="primary" if CONFIG.show_timestamps else "default"),
                classes="setting-row",
            ),
            Horizontal(
                Static("Streaming:", classes="setting-label"),
                Button("Activé" if CONFIG.streaming_enabled else "Désactivé", id="streaming_toggle", variant="primary" if CONFIG.streaming_enabled else "default"),
                classes="setting-row",
            ),
            Horizontal(
                Static("Auto-scroll:", classes="setting-label"),
                Button("Activé" if CONFIG.auto_scroll else "Désactivé", id="autoscroll_toggle", variant="primary" if CONFIG.auto_scroll else "default"),
                classes="setting-row",
            ),
            Horizontal(
                Button("Sauvegarder", id="save_btn", variant="success"),
                Button("Annuler", id="cancel_btn", variant="default"),
                id="settings-buttons",
            ),
            id="settings-screen",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_btn":
            self._save_settings()
            self.app.pop_screen()
            self.app.notify("Paramètres sauvegardés")
        elif event.button.id == "cancel_btn":
            self.app.pop_screen()
        elif event.button.id == "compact_toggle":
            CONFIG.compact_mode = not CONFIG.compact_mode
            event.button.label = "Activé" if CONFIG.compact_mode else "Désactivé"
            event.button.variant = "primary" if CONFIG.compact_mode else "default"
        elif event.button.id == "timestamp_toggle":
            CONFIG.show_timestamps = not CONFIG.show_timestamps
            event.button.label = "Activé" if CONFIG.show_timestamps else "Désactivé"
            event.button.variant = "primary" if CONFIG.show_timestamps else "default"
        elif event.button.id == "streaming_toggle":
            CONFIG.streaming_enabled = not CONFIG.streaming_enabled
            event.button.label = "Activé" if CONFIG.streaming_enabled else "Désactivé"
            event.button.variant = "primary" if CONFIG.streaming_enabled else "default"
        elif event.button.id == "autoscroll_toggle":
            CONFIG.auto_scroll = not CONFIG.auto_scroll
            event.button.label = "Activé" if CONFIG.auto_scroll else "Désactivé"
            event.button.variant = "primary" if CONFIG.auto_scroll else "default"

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "api_url":
            CONFIG.api_base_url = event.value
        elif event.input.id == "api_key":
            CONFIG.openrouter_api_key = event.value

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "default_agent":
            CONFIG.default_agent = event.value if event.value != "auto" else ""

    def _save_settings(self):
        save_config()

    def action_close(self):
        self.app.pop_screen()