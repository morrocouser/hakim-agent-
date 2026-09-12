from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QDockWidget, QSplitter, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QKeySequence, QFont

from desktop.widgets.chat_area import ChatArea
from desktop.widgets.input_widget import InputWidget
from desktop.widgets.agent_sidebar import AgentSidebar
from desktop.widgets.memory_panel import MemoryPanel
from desktop.widgets.status_bar import AxiomStatusBar
from desktop.dialogs.settings_dialog import SettingsDialog
from desktop.dialogs.help_dialog import HelpDialog
from desktop.workers.chat_worker import ChatWorker
from desktop.workers.history_manager import HistoryManager, HistoryEntry
from cli.tui.config import CONFIG, load_config, save_config
from axiom.core.memory import MemoryManager
from axiom.claude.client import OpenRouterClient


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        load_config()
        self.config = CONFIG
        self.memory = MemoryManager()
        self.history = HistoryManager()
        self._agent_forced = ""
        self._model_forced = ""
        self._worker = None
        self._agents_action = None
        self._memory_action = None
        self.setWindowTitle("APEX v4.0 — Orchestrateur Multi-Agents")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)
        self._setup_menu()
        self._setup_ui()
        self._setup_shortcuts()
        self._show_welcome()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._chat_area = ChatArea()
        self._input = InputWidget()

        self._input.submitted.connect(self._on_submit)
        self._input.interrupted.connect(self._on_interrupt)

        layout.addWidget(self._chat_area)
        layout.addWidget(self._input)

        self._agent_dock = QDockWidget("Agents", self)
        self._agent_dock.setWidget(AgentSidebar())
        self._agent_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self._agent_dock.visibilityChanged.connect(self._on_agent_dock_toggle)
        self._agent_sidebar = self._agent_dock.widget()
        self._agent_sidebar.agent_selected.connect(self._on_agent_selected)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._agent_dock)
        self._agent_dock.hide()

        self._memory_dock = QDockWidget("Memoire", self)
        self._memory_dock.setWidget(MemoryPanel())
        self._memory_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self._memory_dock.visibilityChanged.connect(self._on_memory_dock_toggle)
        self._memory_panel = self._memory_dock.widget()
        self.addDockWidget(Qt.RightDockWidgetArea, self._memory_dock)
        self._memory_dock.hide()

        self._status_bar = AxiomStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._load_memory()

    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(
            "QMenuBar{background:#111827;color:#e6edf3;border-bottom:1px solid #1e293b;padding:2px;}"
            "QMenuBar::item:selected{background:#1e293b;border-radius:4px;padding:4px 8px;}"
            "QMenu{background:#161b22;color:#e6edf3;border:1px solid #1e293b;padding:4px;border-radius:6px;}"
            "QMenu::item:selected{background:#1e293b;border-radius:4px;}"
        )

        view_menu = menubar.addMenu("View")
        self._agents_action = QAction("Toggle Agents (F2)", self)
        self._agents_action.setShortcut(QKeySequence("F2"))
        self._agents_action.setCheckable(True)
        self._agents_action.triggered.connect(self._toggle_agents)
        view_menu.addAction(self._agents_action)

        self._memory_action = QAction("Toggle Memoire (F3)", self)
        self._memory_action.setShortcut(QKeySequence("F3"))
        self._memory_action.setCheckable(True)
        self._memory_action.triggered.connect(self._toggle_memory)
        view_menu.addAction(self._memory_action)

        view_menu.addSeparator()
        clear_action = QAction("Effacer chat (Ctrl+L)", self)
        clear_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_action.triggered.connect(self._clear_chat)
        view_menu.addAction(clear_action)

        tools_menu = menubar.addMenu("Tools")
        settings_action = QAction("Parametres (Ctrl+,)", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)

        help_menu = menubar.addMenu("Help")
        help_action = QAction("Raccourcis (F1)", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)
        about_action = QAction("A propos", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_shortcuts(self):
        pass

    def _sanitize_user_input(self, text: str) -> str:
        """Nettoie le texte utilisateur sans altérer le code ou la ponctuation."""
        if not text:
            return ""
        # Supprime les caractères de contrôle non imprimables et octets nuls
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        return sanitized.strip()


    def _sanitize_error_message(self, error: str) -> str:
        """Sanitize error messages to prevent information disclosure."""
        # Remove stack trace information
        sanitized = re.sub(r'Traceback.*?:\n.*?(?=\n\n|\n[A-Z]|\Z)', '', error, flags=re.DOTALL)

        # Remove sensitive patterns (API keys, passwords)
        sanitized = re.sub(r'secret|password|api_key|token|credential', '[REDACTED]', sanitized, flags=re.IGNORECASE)

        # Remove internal file paths and line numbers
        sanitized = re.sub(r'File \"\.\.\/.*?\"', 'File \"[REDACTED]\"', sanitized)

        # Remove exception types with sensitive data
        sanitized = re.sub(r'ValueError: .*secret.*', 'ValueError: [REDACTED]', sanitized, flags=re.IGNORECASE)

        # Clean up extra whitespace and line breaks
        sanitized = '\\n'.join(line.strip() for line in sanitized.split('\\n') if line.strip())

        # Provide user-friendly error message
        if not sanitized or len(sanitized) < 3:
            return "❌ An error occurred during execution"

        return sanitized

    def _show_welcome(self):
        self._chat_area.add_system_message(
            "🤖 APEX v4.0 — Orchestrateur Multi-Agents\n"
            "Tape un message ou /help pour les raccourcis"
        )

    def _on_submit(self, text: str):
        if text.startswith("/"):
            self._handle_command(text)
            return

        # Sanitize user input to prevent command injection
        import re
        sanitized_text = self._sanitize_user_input(text)
        if sanitized_text != text:
            self._chat_area.add_system_message("⚠️ Votre message a été nettoyé pour des raisons de sécurité")
            text = sanitized_text

        self._chat_area.add_user_message(text)
        self.history.add(HistoryEntry(timestamp="", role="user", content=text))
        self._status_bar.set_thinking(True)
        self._input.set_thinking(True)

        self._worker = ChatWorker(
            message=text,
            api_key=self.config.openrouter_api_key,
            agent=self._agent_forced,
            model=self._model_forced,
            memory=self.memory,
        )
        self._worker.finished.connect(self._on_response)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_response(self, response: str, agent: str, score: float, quality: float, status: str):
        self._chat_area.add_assistant_message(response, agent=agent, model=self._model_forced or "auto", score=score, quality=quality, status=status)
        self._status_bar.update_agent(agent)
        self._status_bar.update_score(score, quality)
        self._status_bar.set_thinking(False)
        self._input.set_thinking(False)
        self.history.add(HistoryEntry(timestamp="", role="assistant", content=response, agent=agent, model=self._model_forced, score=score, quality=quality))

    def _on_error(self, error: str):
        # Sanitize error message to prevent information disclosure
        sanitized_error = self._sanitize_error_message(error)
        self._chat_area.add_system_message(f"❌ Erreur: {sanitized_error}")
        self._status_bar.set_error(True)
        self._input.set_thinking(False)

    def _on_interrupt(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.terminate()
            self._chat_area.add_system_message("⚡ Interrompu")
            self._status_bar.set_thinking(False)
            self._input.set_thinking(False)

    def _handle_command(self, text: str):
        parts = text.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/help":
            self._show_help()
        elif cmd == "/clear":
            self._clear_chat()
        elif cmd == "/settings":
            self._show_settings()
        elif cmd == "/quit":
            self.close()
        elif cmd == "/agents":
            self._toggle_agents()
        elif cmd == "/memory":
            self._toggle_memory()
            self._load_memory()
        elif cmd == "/agent":
            if arg:
                self._agent_forced = arg.upper()
                if not self._agent_forced.startswith("AGENT_"):
                    self._agent_forced = f"AGENT_{self._agent_forced}"
                self._chat_area.add_system_message(f"Agent force: {self._agent_forced}")
                self._status_bar.update_agent(self._agent_forced)
            else:
                self._agent_forced = ""
                self._chat_area.add_system_message("Agent: auto (routing par score)")
                self._status_bar.update_agent("auto")
        elif cmd == "/model":
            if arg:
                self._model_forced = arg
                self._chat_area.add_system_message(f"Modele force: {arg}")
                self._status_bar.update_model(arg)
            else:
                self._model_forced = ""
                self._chat_area.add_system_message("Modele: auto (routing par score)")
                self._status_bar.update_model("auto")
        elif cmd == "/score":
            if arg:
                from axiom.core.scoring import score_and_route
                assignment = score_and_route(arg)
                self._chat_area.add_system_message(
                    f"Scoring: {arg}\n"
                    f"  Agent: {assignment.agent.value}\n"
                    f"  Modele: {assignment.model.value}\n"
                    f"  Score: {assignment.score}/10"
                )
            else:
                self._chat_area.add_system_message("Usage: /score <description>")
        elif cmd == "/project":
            if arg:
                self.memory.set_project(arg)
                self._chat_area.add_system_message(f"Projet defini: {arg}")
                self._load_memory()
            else:
                self._chat_area.add_system_message("Usage: /project <nom>")
        else:
            self._chat_area.add_system_message(f"Commande inconnue: {cmd}. Tape /help")

    def _on_agent_selected(self, agent_name: str):
        self._agent_forced = agent_name
        self._status_bar.update_agent(agent_name)
        self._chat_area.add_system_message(f"Agent selectionne: {agent_name}")

    def _toggle_agents(self):
        if self._agent_dock.isVisible():
            self._agent_dock.hide()
            self._agents_action.setChecked(False)
        else:
            self._agent_dock.show()
            self._agents_action.setChecked(True)

    def _toggle_memory(self):
        if self._memory_dock.isVisible():
            self._memory_dock.hide()
            self._memory_action.setChecked(False)
        else:
            self._memory_dock.show()
            self._memory_action.setChecked(True)
            self._load_memory()

    def _on_agent_dock_toggle(self, visible):
        self._agents_action.setChecked(visible)

    def _on_memory_dock_toggle(self, visible):
        self._memory_action.setChecked(visible)

    def _load_memory(self):
        try:
            data = self.memory.export()
            self._memory_panel.update_memory(data)
        except Exception:
            pass

    def _clear_chat(self):
        self._chat_area.clear_messages()
        self._show_welcome()

    def _show_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == SettingsDialog.Accepted:
            self.config = CONFIG
            self._chat_area.add_system_message("Parametres sauvegardes")

    def _show_help(self):
        dialog = HelpDialog(self)
        dialog.exec()

    def _show_about(self):
        QMessageBox.about(
            self,
            "A propos de APEX",
            "<h2>APEX v4.0</h2>"
            "<p>Orchestrateur Multi-Agents avec scoring algorithmique</p>"
            "<p>8 sous-agents specialises avec routage intelligent</p>"
            "<p>Modeles: Google Gemini, Meta Llama (gratuits via OpenRouter)</p>"
            "<hr>"
            "<p><b>Backend:</b> Python + FastAPI</p>"
            "<p><b>Frontend:</b> PySide6 (Qt)</p>"
            "<p><b>API:</b> OpenRouter (modeles gratuits)</p>"
        )

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.terminate()
            self._worker.wait(1000)
        save_config()
        event.accept()
