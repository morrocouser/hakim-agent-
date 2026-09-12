from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QTextBrowser
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import markdown
from pygments.formatters import HtmlFormatter


AGENT_ICONS = {
    "AGENT_ARCHITECT": "architect",
    "AGENT_CODER": "code",
    "AGENT_DEBUGGER": "debug",
    "AGENT_ANALYST": "data",
    "AGENT_WRITER": "write",
    "AGENT_RESEARCHER": "search",
    "AGENT_PLANNER": "plan",
    "AGENT_QUICKSHOT": "bolt",
}


def _md_to_html(text: str) -> str:
    try:
        extensions = ["fenced_code", "codehilite", "tables", "nl2br"]
        md = markdown.Markdown(extensions=extensions, output_format="html5")
        html = md.convert(text)
        if "codehilite" in html:
            formatter = HtmlFormatter(noclasses=True)
            html = html.replace(
                "class=\"codehilite\"",
                f"style=\"{formatter.get_style_defs('')};background:#0d1117;padding:12px;border-radius:6px;border:1px solid #30363d;overflow-x:auto;font-size:13px;\""
            )
        return html
    except Exception:
        return f"<pre>{text}</pre>"


class MessageBubble(QFrame):
    def __init__(self, role: str, content: str, agent: str = "",
                 model: str = "", score: float = 0.0,
                 quality: float = 0.0, status: str = "DONE",
                 parent=None):
        super().__init__(parent)
        self.role = role
        self.setObjectName("message_bubble")
        self._setup_ui(content, agent, model, score, quality, status)

    def _setup_ui(self, content, agent, model, score, quality, status):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        if self.role == "user":
            self._make_user(content, layout)
        elif self.role == "assistant":
            self._make_assistant(content, agent, model, score, quality, status, layout)
        else:
            self._make_system(content, layout)

    def _make_user(self, content, layout):
        frame = QFrame()
        frame.setObjectName("user_msg")
        frame.setStyleSheet("QFrame#user_msg{background:#1a3a1e;border-radius:10px;padding:10px;}")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(14, 10, 14, 10)

        lbl = QLabel(content)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color:#e6edf3;font-size:14px;")
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        fl.addWidget(lbl)
        layout.addWidget(frame)

    def _make_assistant(self, content, agent, model, score, quality, status, layout):
        frame = QFrame()
        frame.setObjectName("assistant_msg")
        frame.setStyleSheet("QFrame#assistant_msg{background:#111827;border:1px solid #1e293b;border-radius:10px;padding:10px;}")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(14, 10, 14, 10)

        agent_short = agent.replace("AGENT_", "").replace("_", " ").title()
        model_short = model.split("/")[-1].replace(":free", "") if model else ""
        quality_color = "#22c55e" if quality >= 8 else "#eab308" if quality >= 6 else "#ef4444"
        status_color = "#22c55e" if status == "DONE" else "#ef4444"
        score_color = "#3b82f6" if score >= 6.6 else "#eab308" if score >= 2.6 else "#94a3b8"

        header = QLabel(
            f'<span style="color:#94a3b8;font-size:12px;">'
            f'🤖 {agent_short} · <span style="color:{score_color}">{model_short}</span>'
            f' · <span style="color:{score_color}">Score:{score:.1f}</span>'
            f' · <span style="color:{quality_color}">Q:{quality:.1f}</span>'
            f' · <span style="color:{status_color}">{status}</span>'
            f'</span>'
        )
        header.setTextFormat(Qt.RichText)
        fl.addWidget(header)

        html = _md_to_html(content)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(
            '<!DOCTYPE html><html><head><style>'
            'body{font-family:Segoe UI,system-ui,sans-serif;font-size:14px;color:#e6edf3;line-height:1.6;margin:0;padding:0;}'
            'pre{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:12px;overflow-x:auto;font-size:13px;color:#e6edf3;font-family:Consolas,"JetBrains Mono",monospace;}'
            'code{background:#1e293b;padding:2px 5px;border-radius:4px;color:#f97583;font-family:Consolas,"JetBrains Mono",monospace;font-size:13px;}'
            'pre code{background:transparent;padding:0;color:#e6edf3;}'
            'blockquote{border-left:3px solid #3b82f6;padding-left:12px;color:#94a3b8;margin:8px 0;}'
            'a{color:#58a6ff;text-decoration:none;}a:hover{text-decoration:underline;}'
            'table{border-collapse:collapse;margin:8px 0;}th,td{border:1px solid #30363d;padding:6px 12px;text-align:left;}th{background:#161b22;}'
            'ul,ol{padding-left:20px;}li{margin:2px 0;}'
            'h1,h2,h3{color:#f1f5f9;margin:12px 0 6px 0;}'
            'hr{border:none;border-top:1px solid #30363d;margin:12px 0;}'
            '</style></head><body>' + html + '</body></html>'
        )
        browser.setMinimumHeight(30)
        browser.setMaximumHeight(10000)
        browser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        browser.setStyleSheet("QTextBrowser{background:transparent;border:none;color:#e6edf3;}")
        browser.setSizePolicy(browser.sizePolicy().horizontalPolicy(), browser.sizePolicy().verticalPolicy())
        fl.addWidget(browser)

        layout.addWidget(frame)

    def _make_system(self, content, layout):
        lbl = QLabel(content)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color:#6e7681;font-style:italic;font-size:13px;padding:4px 8px;")
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(lbl)
