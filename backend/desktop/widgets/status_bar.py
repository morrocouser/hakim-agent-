from PySide6.QtWidgets import QStatusBar, QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import Qt


class AxiomStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet(
            "QStatusBar{background:#111827;color:#94a3b8;border-top:1px solid #1e293b;font-size:12px;}"
        )

        self._agent_label = QLabel("  🤖 Auto")
        self._model_label = QLabel("auto")
        self._score_label = QLabel("")
        self._status_label = QLabel("")

        self.addWidget(self._agent_label, 1)
        self.addWidget(self._model_label, 1)
        self.addWidget(self._score_label, 1)
        self.addWidget(self._status_label, 0)

    def update_agent(self, agent: str):
        icons = {
            "AGENT_ARCHITECT": "🏗", "AGENT_CODER": "💻", "AGENT_DEBUGGER": "🐛",
            "AGENT_ANALYST": "📊", "AGENT_WRITER": "✍", "AGENT_RESEARCHER": "🔍",
            "AGENT_PLANNER": "🎯", "AGENT_QUICKSHOT": "⚡", "auto": "🤖",
        }
        icon = icons.get(agent, "🤖")
        name = agent.replace("AGENT_", "").replace("_", " ").title() if agent != "auto" else "Auto"
        self._agent_label.setText(f"  {icon} {name}")

    def update_model(self, model: str):
        if model == "auto":
            self._model_label.setText("auto")
        else:
            short = model.split("/")[-1].replace(":free", "")
            self._model_label.setText(short)

    def update_score(self, score: float, quality: float = 0.0):
        if score > 0:
            color = "#3b82f6" if score >= 6.6 else "#eab308" if score >= 2.6 else "#94a3b8"
            qcolor = "#22c55e" if quality >= 8 else "#eab308" if quality >= 6 else "#ef4444"
            self._score_label.setText(
                f'  <span style="color:{color}">Score:{score:.1f}</span>'
                f'  <span style="color:{qcolor}">Q:{quality:.1f}</span>'
            )
            self._score_label.setTextFormat(Qt.RichText)

    def set_thinking(self, thinking: bool):
        if thinking:
            self._status_label.setText('  <span style="color:#eab308">● En reflexion...</span>')
            self._status_label.setTextFormat(Qt.RichText)
        else:
            self._status_label.setText('  <span style="color:#22c55e">● Pret</span>')
            self._status_label.setTextFormat(Qt.RichText)

    def set_error(self, error: bool):
        if error:
            self._status_label.setText('  <span style="color:#ef4444">● Erreur</span>')
            self._status_label.setTextFormat(Qt.RichText)
        else:
            self.set_thinking(False)

    def set_streaming(self, streaming: bool):
        if streaming:
            self._status_label.setText('  <span style="color:#58a6ff">● Streaming...</span>')
            self._status_label.setTextFormat(Qt.RichText)
        else:
            self.set_thinking(False)
