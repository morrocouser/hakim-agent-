from textual.widgets import Static
from textual.containers import Horizontal
from textual.reactive import reactive
from cli.tui.config import CONFIG


class StatusBar(Static):
    """Barre de statut: agent | modèle | score | tokens mémoire"""

    agent: reactive[str] = reactive("auto")
    model: reactive[str] = reactive("auto")
    score: reactive[float] = reactive(0.0)
    quality: reactive[float] = reactive(0.0)
    status: reactive[str] = reactive("READY")
    memory_tokens: reactive[int] = reactive(0)

    def compose(self):
        yield Horizontal(
            Static("", id="status_agent", classes="header-left"),
            Static("", id="status_model", classes="header-center"),
            Static("", id="status_score", classes="header-right"),
            id="header"
        )

    def watch_agent(self, value: str):
        self._update_agent()

    def watch_model(self, value: str):
        self._update_model()

    def watch_score(self, value: float):
        self._update_score()

    def watch_quality(self, value: float):
        self._update_quality()

    def watch_status(self, value: str):
        self._update_status()

    def watch_memory_tokens(self, value: int):
        self._update_memory()

    def _update_agent(self):
        el = self.query_one("#status_agent", Static)
        agent_short = self.agent.replace("AGENT_", "").replace("_", " ")
        icon = self._get_agent_icon(self.agent)
        el.update(f"{icon} [bold]{agent_short}[/bold]")

    def _update_model(self):
        el = self.query_one("#status_model", Static)
        if self.model == "auto":
            el.update("[dim]auto[/dim]")
        else:
            model_short = self.model.split("/")[-1].replace(":free", "")
            el.update(f"[dim]via[/dim] [bold]{model_short}[/bold]")

    def _update_score(self):
        el = self.query_one("#status_score", Static)
        if self.score > 0:
            color = "green" if self.score >= 6.6 else "yellow" if self.score >= 2.6 else "cyan"
            el.update(f"[{color}]Score: {self.score:.1f}[/{color}]")
        else:
            el.update("")

    def _update_quality(self):
        pass  # Intégré dans score

    def _update_status(self):
        el = self.query_one("#status_agent", Static)
        status_colors = {
            "READY": "green",
            "THINKING": "yellow",
            "STREAMING": "cyan",
            "ERROR": "red",
        }
        color = status_colors.get(self.status, "white")
        # On met à jour le statut dans agent
        current = str(el._renderable) if hasattr(el, '_renderable') else ""
        if "●" not in current:
            el.update(f"[{color}]●[/{color}] {current}")

    def _update_memory(self):
        pass  # À implémenter si besoin

    def _get_agent_icon(self, agent: str) -> str:
        icons = {
            "AGENT_ARCHITECT": "🏗️",
            "AGENT_CODER": "💻",
            "AGENT_DEBUGGER": "🐛",
            "AGENT_ANALYST": "📊",
            "AGENT_WRITER": "✍️",
            "AGENT_RESEARCHER": "🔍",
            "AGENT_PLANNER": "🎯",
            "AGENT_QUICKSHOT": "⚡",
            "auto": "🤖",
        }
        return icons.get(agent, "🤖")

    def set_thinking(self, thinking: bool):
        self.status = "THINKING" if thinking else "READY"

    def set_streaming(self, streaming: bool):
        self.status = "STREAMING" if streaming else "READY"

    def set_error(self, error: bool):
        self.status = "ERROR" if error else "READY"