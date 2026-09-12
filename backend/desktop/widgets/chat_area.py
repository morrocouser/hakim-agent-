from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from desktop.widgets.message_bubble import MessageBubble


class ChatArea(QScrollArea):
    message_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea{background:#0a0e1a;border:none;}")
        self._container = QWidget()
        self._container.setStyleSheet("background:#0a0e1a;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(16, 8, 16, 8)
        self._layout.setSpacing(4)
        self._layout.addStretch()
        self.setWidget(self._container)
        self._messages = []

    def add_user_message(self, content: str):
        bubble = MessageBubble("user", content)
        self._layout.insertWidget(self._layout.count() - 1, bubble)
        self._messages.append(bubble)
        self._scroll_to_bottom()

    def add_assistant_message(self, content: str, agent: str = "",
                              model: str = "", score: float = 0.0,
                              quality: float = 0.0, status: str = "DONE",
                              error: str = None):
        if error:
            bubble = MessageBubble("assistant", f"❌ Erreur: {error}", agent=agent, model=model, score=score, quality=0, status="FAILED")
        else:
            bubble = MessageBubble("assistant", content, agent=agent, model=model, score=score, quality=quality, status=status)
        self._layout.insertWidget(self._layout.count() - 1, bubble)
        self._messages.append(bubble)
        self._scroll_to_bottom()

    def add_system_message(self, content: str):
        bubble = MessageBubble("system", content)
        self._layout.insertWidget(self._layout.count() - 1, bubble)
        self._messages.append(bubble)
        self._scroll_to_bottom()

    def clear_messages(self):
        for msg in self._messages:
            self._layout.removeWidget(msg)
            msg.deleteLater()
        self._messages.clear()

    def _scroll_to_bottom(self):
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())
