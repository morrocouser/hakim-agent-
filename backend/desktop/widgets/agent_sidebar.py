from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QIcon


AGENT_ORDER = [
    "AGENT_ARCHITECT", "AGENT_CODER", "AGENT_DEBUGGER",
    "AGENT_ANALYST", "AGENT_WRITER", "AGENT_RESEARCHER",
    "AGENT_PLANNER", "AGENT_QUICKSHOT",
]

AGENT_ICONS = {
    "AGENT_ARCHITECT": "🏗",
    "AGENT_CODER": "💻",
    "AGENT_DEBUGGER": "🐛",
    "AGENT_ANALYST": "📊",
    "AGENT_WRITER": "✍",
    "AGENT_RESEARCHER": "🔍",
    "AGENT_PLANNER": "🎯",
    "AGENT_QUICKSHOT": "⚡",
}

MODEL_SHORT = {
    "google/gemini-2.5-pro-exp-03-25:free": "Gemini Pro",
    "meta-llama/llama-3.1-8b-instruct:free": "Llama 8B",
    "meta-llama/llama-3.2-3b-instruct:free": "Llama 3B",
    "google/gemini-2.0-flash-exp:free": "Gemini Flash",
}


class AgentSidebar(QFrame):
    agent_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("agent_sidebar")
        self.setFixedWidth(260)
        self.setStyleSheet(
            "QFrame#agent_sidebar{background:#111827;border-right:1px solid #1e293b;}"
        )
        self._agents_data = {}
        self._selected = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(" AGENTS")
        header.setFixedHeight(36)
        header.setStyleSheet(
            "QLabel{background:#0d1117;color:#3b82f6;font-weight:bold;font-size:13px;"
            "border-bottom:1px solid #1e293b;padding-left:12px;}"
        )
        layout.addWidget(header)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(False)
        self._tree.setIndentation(0)
        self._tree.setStyleSheet(
            "QTreeWidget{background:#111827;color:#e6edf3;border:none;font-size:13px;padding:4px;}"
            "QTreeWidget::item{padding:8px 12px;border-radius:6px;margin:1px 4px;}"
            "QTreeWidget::item:selected{background:#1e293b;color:#3b82f6;}"
            "QTreeWidget::item:hover{background:#1a1f2e;}"
        )
        self._tree.itemClicked.connect(self._on_click)
        layout.addWidget(self._tree)

    def set_agents(self, agents: dict):
        self._agents_data = agents
        self._tree.clear()
        for name in AGENT_ORDER:
            info = agents.get(name, {})
            icon = AGENT_ICONS.get(name, "🤖")
            label = info.get("label", name.replace("AGENT_", "").title())
            model = info.get("default_model", "")
            model_short = MODEL_SHORT.get(model, model.split("/")[-1].replace(":free", "") if model else "")
            item = QTreeWidgetItem([f"{icon}  {label}  ({model_short})"])
            item.setData(0, Qt.UserRole, name)
            self._tree.addTopLevelItem(item)

    def _on_click(self, item, col):
        name = item.data(0, Qt.UserRole)
        if name:
            self._selected = name
            self.agent_selected.emit(name)

    def get_selected(self):
        return self._selected

    def clear_selection(self):
        self._selected = None
        self._tree.clearSelection()
