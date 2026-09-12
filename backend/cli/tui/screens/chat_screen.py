from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Horizontal, Vertical
from cli.tui.widgets.chat_view import ChatView, ThinkingIndicator
from cli.tui.widgets.input_bar import InputBar
from cli.tui.widgets.status_bar import StatusBar
from cli.tui.widgets.agent_panel import AgentPanel
from cli.tui.widgets.memory_panel import MemoryPanel


class ChatScreen(Screen):
    """Écran principal de conversation."""

    BINDINGS = [
        ("f1", "help", "Aide"),
        ("f2", "toggle_agents", "Agents"),
        ("f3", "toggle_memory", "Mémoire"),
        ("f4", "toggle_compact", "Compact"),
        ("ctrl+l", "clear", "Effacer"),
        ("ctrl+q", "quit", "Quitter"),
    ]

    def compose(self):
        yield Horizontal(
            # Sidebar Agents (F2)
            AgentPanel(id="sidebar", classes="-visible"),
            # Zone principale
            Vertical(
                StatusBar(id="status_bar"),
                ChatView(id="chat_view"),
                ThinkingIndicator(id="thinking"),
                InputBar(id="input_bar"),
                id="main",
            ),
            # Sidebar Mémoire (F3)
            MemoryPanel(id="memory_panel", classes="-visible"),
            id="app-grid",
        )

    def on_mount(self):
        self._sidebar_visible = False
        self._memory_visible = False

    def action_toggle_agents(self):
        sidebar = self.query_one("#sidebar", AgentPanel)
        self._sidebar_visible = not self._sidebar_visible
        if self._sidebar_visible:
            sidebar.add_class("visible")
        else:
            sidebar.remove_class("visible")

    def action_toggle_memory(self):
        panel = self.query_one("#memory_panel", MemoryPanel)
        self._memory_visible = not self._memory_visible
        if self._memory_visible:
            panel.add_class("visible")
        else:
            panel.remove_class("visible")

    def action_toggle_compact(self):
        # Toggle compact mode
        self.app.config.compact_mode = not self.app.config.compact_mode
        from cli.tui.config import save_config
        save_config()
        self.app.notify(f"Mode compact: {'activé' if self.app.config.compact_mode else 'désactivé'}")

    def action_clear(self):
        chat = self.query_one("#chat_view", ChatView)
        chat.clear()
        self.app.notify("Conversation effacée")

    def action_help(self):
        self.app.push_screen("help")

    def action_quit(self):
        self.app.exit()