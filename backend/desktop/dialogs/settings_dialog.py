from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGroupBox, QFormLayout, QCheckBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from axiom.core.agents import AGENT_CONFIGS
from axiom.models.schemas import AgentName


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Parametres APEX")
        self.setMinimumSize(520, 480)
        self.setStyleSheet(self._style())
        self._setup_ui()

    def _style(self):
        return """
        QDialog{background:#0a0e1a;color:#e6edf3;}
        QGroupBox{background:#111827;border:1px solid #1e293b;border-radius:8px;margin-top:12px;
                  padding:16px 12px 12px 12px;color:#e6edf3;font-weight:bold;}
        QGroupBox::title{subcontrol-origin:margin;left:16px;padding:0 8px;}
        QLabel{color:#94a3b8;font-size:13px;}
        QLineEdit{background:#161b22;border:1px solid #30363d;border-radius:6px;
                  color:#e6edf3;padding:8px 12px;font-size:13px;}
        QLineEdit:focus{border:1px solid #3b82f6;}
        QComboBox{background:#161b22;border:1px solid #30363d;border-radius:6px;
                  color:#e6edf3;padding:8px 12px;font-size:13px;}
        QComboBox::drop-down{border:none;width:24px;}
        QComboBox QAbstractItemView{background:#161b22;color:#e6edf3;selection-background-color:#1e293b;}
        QCheckBox{color:#e6edf3;font-size:13px;}
        QCheckBox::indicator{width:18px;height:18px;border-radius:4px;border:1px solid #30363d;background:#161b22;}
        QCheckBox::indicator:checked{background:#22c55e;border-color:#22c55e;}
        QPushButton{background:#3b82f6;color:white;border:none;border-radius:6px;padding:8px 20px;
                    font-weight:bold;font-size:13px;}
        QPushButton:hover{background:#2563eb;}
        QPushButton#cancel{background:#30363d;}
        QPushButton#cancel:hover{background:#3d444d;}
        """

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabWidget::pane{background:#111827;border:1px solid #1e293d;border-radius:6px;padding:8px;}"
            "QTabBar::tab{background:#161b22;color:#94a3b8;padding:8px 20px;border:1px solid #1e293d;"
            "border-bottom:none;border-top-left-radius:6px;border-top-right-radius:6px;margin-right:2px;}"
            "QTabBar::tab:selected{background:#111827;color:#3b82f6;border-bottom:2px solid #3b82f6;}"
        )

        api_tab = QWidget()
        api_layout = QFormLayout(api_tab)
        api_layout.setSpacing(12)
        self._api_url = QLineEdit(self.config.api_base_url)
        self._api_url.setPlaceholderText("http://localhost:8000/api/v1")
        api_layout.addRow("API Base URL:", self._api_url)
        self._api_key = QLineEdit(self.config.openrouter_api_key)
        self._api_key.setEchoMode(QLineEdit.Password)
        self._api_key.setPlaceholderText("sk-or-v1-...")
        api_layout.addRow("OpenRouter API Key:", self._api_key)

        agents = ["(Auto)"] + [name.value for name in AgentName]
        self._default_agent = QComboBox()
        self._default_agent.addItems(agents)
        if self.config.default_agent:
            idx = agents.index(self.config.default_agent) if self.config.default_agent in agents else 0
            self._default_agent.setCurrentIndex(idx)
        api_layout.addRow("Agent par defaut:", self._default_agent)
        tabs.addTab(api_tab, "API & Modeles")

        ui_tab = QWidget()
        ui_layout = QFormLayout(ui_tab)
        ui_layout.setSpacing(12)
        self._compact = QCheckBox("Mode compact (barre laterale)")
        self._compact.setChecked(self.config.compact_mode)
        ui_layout.addRow(self._compact)
        self._timestamps = QCheckBox("Afficher les timestamps")
        self._timestamps.setChecked(self.config.show_timestamps)
        ui_layout.addRow(self._timestamps)
        self._streaming = QCheckBox("Activer le streaming")
        self._streaming.setChecked(self.config.streaming_enabled)
        ui_layout.addRow(self._streaming)
        self._autoscroll = QCheckBox("Auto-scroll en bas")
        self._autoscroll.setChecked(self.config.auto_scroll)
        ui_layout.addRow(self._autoscroll)
        tabs.addTab(ui_tab, "Interface")

        layout.addWidget(tabs)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setObjectName("cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("Sauvegarder")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        self.config.api_base_url = self._api_url.text().strip() or "http://localhost:8000/api/v1"
        self.config.openrouter_api_key = self._api_key.text().strip()
        agent = self._default_agent.currentText()
        self.config.default_agent = "" if agent == "(Auto)" else agent
        self.config.compact_mode = self._compact.isChecked()
        self.config.show_timestamps = self._timestamps.isChecked()
        self.config.streaming_enabled = self._streaming.isChecked()
        self.config.auto_scroll = self._autoscroll.isChecked()
        from cli.tui.config import save_config
        save_config()
        self.accept()
