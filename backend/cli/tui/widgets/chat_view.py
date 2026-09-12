from textual.widgets import Static, RichLog
from textual.containers import VerticalScroll
from textual.message import Message
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.console import Console
from io import StringIO
from typing import Optional
from datetime import datetime


class ChatView(VerticalScroll):
    """Zone de conversation avec support markdown, code blocks, streaming."""

    BINDINGS = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_scroll = True
        self._streaming_buffer = ""
        self._streaming_active = False
        self._last_assistant_index = -1

    def compose(self):
        yield RichLog(id="chat_log", highlight=True, markup=True, wrap=True)

    def on_mount(self):
        log = self.query_one("#chat_log", RichLog)
        log.auto_scroll = True

    def add_user_message(self, content: str, timestamp: bool = True):
        log = self.query_one("#chat_log", RichLog)
        prefix = self._format_prefix("Vous", "user")
        log.write(f"{prefix}{content}")
        self._scroll_if_needed()

    def add_assistant_message(
        self,
        content: str,
        agent: str = "",
        model: str = "",
        score: float = 0.0,
        quality: float = 0.0,
        status: str = "DONE",
        error: str = None,
        timestamp: bool = True
    ):
        log = self.query_one("#chat_log", RichLog)
        header = self._format_header(agent, model, score, quality, status)
        prefix = self._format_prefix("APEX", "assistant", header)
        
        if error:
            log.write(f"{prefix}[red]Erreur: {error}[/red]")
        else:
            log.write(f"{prefix}{content}")
        self._scroll_if_needed()

    def add_system_message(self, content: str):
        log = self.query_one("#chat_log", RichLog)
        log.write(f"[dim italic]{content}[/dim italic]")
        self._scroll_if_needed()

    def start_streaming(self, agent: str = "", model: str = "", score: float = 0.0):
        """Démarre le mode streaming pour un message assistant."""
        log = self.query_one("#chat_log", RichLog)
        header = self._format_header(agent, model, score, 0.0, "STREAMING")
        prefix = self._format_prefix("APEX", "assistant", header)
        log.write(prefix, end="")
        self._streaming_active = True
        self._streaming_buffer = ""

    def stream_chunk(self, chunk: str):
        """Ajoute un chunk au message en streaming."""
        log = self.query_one("#chat_log", RichLog)
        self._streaming_buffer += chunk
        log.write(chunk, end="")
        self._scroll_if_needed()

    def end_streaming(self, agent: str = "", model: str = "", score: float = 0.0, quality: float = 0.0, status: str = "DONE"):
        """Termine le streaming et ajoute le header final."""
        log = self.query_one("#chat_log", RichLog)
        # Le contenu est déjà affiché, on ajoute juste la fin de ligne
        log.write("")  # nouvelle ligne
        self._streaming_active = False
        self._scroll_if_needed()

    def interrupt_streaming(self):
        """Interrompt le streaming en cours."""
        if self._streaming_active:
            log = self.query_one("#chat_log", RichLog)
            log.write("\n[yellow]⚡ Interrompu[/yellow]")
            self._streaming_active = False
            self._scroll_if_needed()

    def clear(self):
        log = self.query_one("#chat_log", RichLog)
        log.clear()

    def _format_prefix(self, sender: str, msg_type: str, header: str = "") -> str:
        ts = f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim] " if self.app.CONFIG.show_timestamps else ""
        if msg_type == "user":
            return f"{ts}[bold green]{sender} ›[/bold green] "
        elif msg_type == "assistant":
            return f"{ts}[bold cyan]{sender}[/bold cyan]{header} › "
        return f"{ts}{sender} › "

    def _format_header(self, agent: str, model: str, score: float, quality: float, status: str) -> str:
        parts = []
        if agent:
            agent_short = agent.replace("AGENT_", "")
            parts.append(f"[dim]{agent_short}[/dim]")
        if model:
            model_short = model.split("/")[-1].replace(":free", "")
            parts.append(f"[dim]{model_short}[/dim]")
        if score:
            parts.append(f"[dim]Score:{score:.1f}[/dim]")
        if quality:
            color = "green" if quality >= 8 else "yellow" if quality >= 6 else "red"
            parts.append(f"[{color}]Q:{quality:.1f}[/{color}]")
        status_color = "green" if status == "DONE" else "red" if status == "FAILED" else "yellow"
        parts.append(f"[{status_color}]{status}[/{status_color}]")
        return f" [{' · '.join(parts)}]" if parts else ""

    def _scroll_if_needed(self):
        if self.auto_scroll and self.app.config.auto_scroll:
            self.scroll_end(animate=False)

    def action_copy_last_code(self):
        """Copie le dernier bloc de code affiché."""
        log = self.query_one("#chat_log", RichLog)
        # TODO: implémenter extraction code block
        self.app.notify("Fonctionnalité à implémenter")


class ThinkingIndicator(Static):
    """Indicateur animé 'APEX réfléchit...'"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._index = 0
        self._timer = None

    def start(self):
        self._timer = self.set_interval(0.1, self._animate)

    def stop(self):
        if self._timer:
            self._timer.stop()
            self._timer = None
        self.update("")

    def _animate(self):
        self._index = (self._index + 1) % len(self._frames)
        self.update(f"[dim]{self._frames[self._index]} APEX réfléchit...[/dim]")