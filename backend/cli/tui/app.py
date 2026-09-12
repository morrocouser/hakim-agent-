from textual.app import App, ComposeResult
from textual.binding import Binding
from textual import on, work
from typing import Optional
import asyncio
import os

from cli.tui.config import CONFIG, load_config, save_config
from cli.tui.actions.api_client import APIClient, ChatMessage
from cli.tui.actions.history import HistoryManager, HistoryEntry
from cli.tui.screens.chat_screen import ChatScreen
from cli.tui.screens.help_screen import HelpScreen
from cli.tui.screens.settings_screen import SettingsScreen
from cli.tui.widgets.chat_view import ChatView, ThinkingIndicator
from cli.tui.widgets.input_bar import InputBar
from cli.tui.widgets.status_bar import StatusBar
from cli.tui.widgets.agent_panel import AgentPanel
from cli.tui.widgets.memory_panel import MemoryPanel


class AxiomTUI(App):
    """AXIOM v4.0 — TUI Orchestrateur Multi-Agents"""

    TITLE = "APEX v4.0"
    SUB_TITLE = "Orchestrateur Multi-Agents"

    CSS_PATH = os.path.join(os.path.dirname(__file__), "css", "axiom.tcss")

    SCREENS = {
        "chat": ChatScreen,
        "help": HelpScreen,
        "settings": SettingsScreen,
    }

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quitter"),
        Binding("ctrl+l", "clear", "Effacer"),
    ]

    def __init__(self):
        super().__init__()
        load_config()
        self.config = CONFIG
        self.api = APIClient(CONFIG.api_base_url)
        self.history = HistoryManager(CONFIG.history_file)
        self._agent_forced: Optional[str] = None
        self._model_forced: Optional[str] = None
        self._streaming = False

    def compose(self) -> ComposeResult:
        yield ChatScreen()

    async def on_mount(self):
        await self._init_agents()
        self._show_welcome()

    def _show_welcome(self):
        chat = self.query_one("#chat_view", ChatView)
        chat.add_system_message(
            "[bold cyan]APEX v4.0[/bold cyan] [dim]— Orchestrateur Multi-Agents[/dim]\n"
            "[dim]Tape un message ou /help pour les raccourcis[/dim]"
        )

    async def _init_agents(self):
        try:
            agents = await self.api.get_agents()
            panel = self.query_one("#sidebar", AgentPanel)
            panel.update_agents(agents)
        except Exception:
            pass

    async def _load_memory(self):
        try:
            memory = await self.api.get_memory()
            panel = self.query_one("#memory_panel", MemoryPanel)
            panel.update_memory(memory)
        except Exception:
            pass

    @on(InputBar.Submit)
    async def handle_submit(self, event: InputBar.Submit):
        text = event.text.strip()
        if not text:
            return

        chat = self.query_one("#chat_view", ChatView)
        input_bar = self.query_one("#input_bar", InputBar)
        status = self.query_one("#status_bar", StatusBar)

        # Commandes slash
        if text.startswith("/"):
            await self._handle_command(text)
            input_bar.add_to_history(text)
            return

        # Ajouter message utilisateur
        chat.add_user_message(text)
        input_bar.add_to_history(text)
        self.history.add(HistoryEntry(
            timestamp="",
            role="user",
            content=text,
        ))

        # Envoyer à l'orchestrateur
        status.set_thinking(True)
        thinking = self.query_one("#thinking", ThinkingIndicator)
        thinking.start()

        try:
            result = await self.api.chat(text, self._agent_forced, self._model_forced)
            thinking.stop()

            chat.add_assistant_message(
                result.content,
                agent=result.agent or "",
                model=result.model or "",
                score=result.score or 0.0,
                quality=result.quality or 0.0,
                status=result.status or "DONE",
                error=result.error,
            )

            # Mettre à jour status bar
            status.agent = result.agent or "auto"
            status.model = result.model or "auto"
            status.score = result.score or 0.0

            # Enregistrer dans historique
            self.history.add(HistoryEntry(
                timestamp="",
                role="assistant",
                content=result.content,
                agent=result.agent,
                model=result.model,
                score=result.score,
                quality=result.quality,
            ))

            # Rafraîchir mémoire
            await self._load_memory()

        except Exception as e:
            thinking.stop()
            chat.add_system_message(f"[red]Erreur API:[/red] {str(e)}")
            status.set_error(True)

        status.set_thinking(False)

    @on(InputBar.HistoryNavigate)
    def handle_history_nav(self, event: InputBar.HistoryNavigate):
        input_bar = self.query_one("#input_bar", InputBar)
        input_bar.navigate_history(event.direction)

    async def _handle_command(self, text: str):
        chat = self.query_one("#chat_view", ChatView)
        parts = text.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/help":
            self.push_screen("help")

        elif cmd == "/clear":
            chat.clear()
            self._show_welcome()

        elif cmd == "/settings":
            self.push_screen("settings")

        elif cmd == "/agents":
            agents = await self.api.get_agents()
            chat.add_system_message("[bold]Sous-Agents disponibles:[/bold]")
            for name, info in agents.items():
                chat.add_system_message(
                    f"  {info['icon']} [bold cyan]{name}[/bold cyan] "
                    f"[dim]({info['default_model']})[/dim]\n"
                    f"    {info['speciality']}"
                )

        elif cmd == "/memory":
            memory = await self.api.get_memory()
            chat.add_system_message(f"[bold]Mémoire 3 niveaux:[/bold] {memory.get('tokens_estimate', 0)} tokens")
            panel = self.query_one("#memory_panel", MemoryPanel)
            panel.update_memory(memory)

        elif cmd == "/agent":
            if arg:
                self._agent_forced = arg.upper()
                if not self._agent_forced.startswith("AGENT_"):
                    self._agent_forced = f"AGENT_{self._agent_forced}"
                chat.add_system_message(f"[cyan]Agent forcé:[/cyan] {self._agent_forced}")
            else:
                self._agent_forced = None
                chat.add_system_message("[cyan]Agent:[/cyan] auto (routing par score)")

        elif cmd == "/model":
            if arg:
                self._model_forced = arg
                chat.add_system_message(f"[cyan]Modèle forcé:[/cyan] {arg}")
            else:
                self._model_forced = None
                chat.add_system_message("[cyan]Modèle:[/cyan] auto (routing par score)")

        elif cmd == "/project":
            if arg:
                try:
                    await self.api.set_project(arg)
                    chat.add_system_message(f"[green]Projet défini:[/green] {arg}")
                except Exception as e:
                    chat.add_system_message(f"[red]Erreur:[/red] {e}")
            else:
                chat.add_system_message("[yellow]Usage:[/yellow] /project <nom du projet>")

        elif cmd == "/score":
            if arg:
                result = await self.api.score_task(arg)
                chat.add_system_message(
                    f"[bold]Scoring:[/bold] {arg}\n"
                    f"  Agent: [cyan]{result['agent']}[/cyan]\n"
                    f"  Modèle: [cyan]{result['model']}[/cyan]\n"
                    f"  Score: [bold]{result['score']}/10[/bold]"
                )
            else:
                chat.add_system_message("[yellow]Usage:[/yellow] /score <description>")

        elif cmd == "/quit":
            self.exit()

        else:
            chat.add_system_message(f"[yellow]Commande inconnue:[/yellow] {cmd}. Tape /help")

    def action_clear(self):
        chat = self.query_one("#chat_view", ChatView)
        chat.clear()
        self._show_welcome()

    async def action_quit(self):
        await self.api.close()
        self.exit()
