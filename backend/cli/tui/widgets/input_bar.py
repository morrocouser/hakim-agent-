from textual.widgets import Input, Static
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.events import Key
from typing import List, Optional
from datetime import datetime


class InputBar(Vertical):
    """Barre de saisie avec historique, complétion, raccourcis."""

    class Submit(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class HistoryNavigate(Message):
        def __init__(self, direction: int) -> None:
            self.direction = direction  # -1 = up, 1 = down
            super().__init__()

    BINDINGS = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history: List[str] = []
        self.history_index = -1
        self.current_input = ""
        self._completion_visible = False
        self._completions = [
            "/help", "/agents", "/memory", "/clear", "/settings",
            "/agent", "/model", "/project", "/stack", "/decision",
            "agent_architect", "agent_coder", "agent_debugger",
            "agent_analyst", "agent_writer", "agent_researcher",
            "agent_planner", "agent_quickshot",
        ]

    def compose(self):
        yield Horizontal(
            Input(
                id="input_field",
                placeholder="Message APEX... (Entrée=envoyer, Maj+Entrée=nouvelle ligne, Tab=complétion)",
                classes="input-field",
            ),
            Static("", id="shortcuts", classes="shortcuts"),
            id="input_container"
        )
        yield Static("", id="input_hint", classes="input-hint")

    def on_mount(self):
        input_field = self.query_one("#input_field", Input)
        input_field.focus()
        self._update_shortcuts()
        self._load_history()

    def _update_shortcuts(self):
        shortcuts = self.query_one("#shortcuts", Static)
        shortcuts.update("⏎ Envoyer  ⇧⏎ Ligne  ^C Interrompre  ↑↓ Historique  Tab Complétion  F1 Aide  F2 Agents  F3 Mémoire")

    def _load_history(self):
        # L'historique est géré par HistoryManager dans l'app
        pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self.post_message(self.Submit(text))
            event.input.value = ""
            self.current_input = ""
            self.history_index = -1

    def on_key(self, event: Key) -> None:
        if event.key == "up":
            self.post_message(self.HistoryNavigate(-1))
            event.prevent_default()
        elif event.key == "down":
            self.post_message(self.HistoryNavigate(1))
            event.prevent_default()
        elif event.key == "tab":
            self._show_completion()
            event.prevent_default()
        elif event.key == "escape":
            self._hide_completion()
            event.prevent_default()
        elif event.key == "ctrl+c":
            # Géré au niveau app
            pass
        elif event.key == "ctrl+l":
            self.app.action_clear()
            event.prevent_default()

    def add_to_history(self, text: str):
        if text and (not self.history or self.history[-1] != text):
            self.history.append(text)
            if len(self.history) > 1000:
                self.history = self.history[-1000:]

    def navigate_history(self, direction: int):
        if not self.history:
            return
        input_field = self.query_one("#input_field", Input)
        
        if direction == -1:  # Up
            if self.history_index == -1:
                self.current_input = input_field.value
                self.history_index = len(self.history) - 1
            elif self.history_index > 0:
                self.history_index -= 1
            if self.history_index >= 0:
                input_field.value = self.history[self.history_index]
        else:  # Down
            if self.history_index >= 0:
                self.history_index += 1
                if self.history_index >= len(self.history):
                    self.history_index = -1
                    input_field.value = self.current_input
                else:
                    input_field.value = self.history[self.history_index]

    def _show_completion(self):
        # TODO: implémenter popup de complétion
        pass

    def _hide_completion(self):
        self._completion_visible = False

    def set_placeholder(self, text: str):
        input_field = self.query_one("#input_field", Input)
        input_field.placeholder = text

    def focus_input(self):
        input_field = self.query_one("#input_field", Input)
        input_field.focus()