from PySide6.QtWidgets import QFrame, QTextEdit, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QTextCursor, QKeySequence


class InputWidget(QFrame):
    submitted = Signal(str)
    interrupted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("input_frame")
        self.setStyleSheet("QFrame#input_frame{background:#0a0e1a;border-top:1px solid #1e293b;}")
        self.setFixedHeight(70)
        self._history = []
        self._history_idx = -1
        self._current_text = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(8)

        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("Message APEX... (Ctrl+Enter=envoyer, Ctrl+I=interrompre)")
        self._text_edit.setAcceptRichText(False)
        self._text_edit.setMaximumHeight(50)
        self._text_edit.setMinimumHeight(36)
        font = QFont("Segoe UI", 13)
        self._text_edit.setFont(font)
        self._text_edit.setStyleSheet(
            "QTextEdit{background:#161b22;border:1px solid #30363d;border-radius:8px;"
            "color:#e6edf3;padding:8px 12px;selection-background-color:#3b82f6;}"
            "QTextEdit:focus{border:1px solid #3b82f6;}"
        )
        self._text_edit.installEventFilter(self)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._send_btn = QPushButton("⏎")
        self._send_btn.setFixedSize(32, 32)
        self._send_btn.setToolTip("Envoyer (Ctrl+Enter)")
        self._send_btn.setStyleSheet(
            "QPushButton{background:#22c55e;color:white;border:none;border-radius:6px;font-size:16px;font-weight:bold;}"
            "QPushButton:hover{background:#16a34a;}"
            "QPushButton:pressed{background:#15803d;}"
        )
        self._send_btn.clicked.connect(self._on_send)

        self._stop_btn = QPushButton("■")
        self._stop_btn.setFixedSize(32, 32)
        self._stop_btn.setToolTip("Interrompre (Ctrl+I)")
        self._stop_btn.setStyleSheet(
            "QPushButton{background:#ef4444;color:white;border:none;border-radius:6px;font-size:12px;}"
            "QPushButton:hover{background:#dc2626;}"
        )
        self._stop_btn.clicked.connect(self.interrupted)
        self._stop_btn.hide()

        btn_row.addWidget(self._stop_btn)
        btn_row.addWidget(self._send_btn)

        layout.addWidget(self._text_edit)
        layout.addLayout(btn_row)

    def eventFilter(self, obj, event):
        if obj == self._text_edit and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._on_send()
                return True
            elif event.key() == Qt.Key_Return and event.modifiers() == Qt.NoModifier:
                self._on_send()
                return True
            elif event.key() == Qt.Key_Up and not self._text_edit.toPlainText().strip():
                self._navigate_history(-1)
                return True
            elif event.key() == Qt.Key_Down and not self._text_edit.toPlainText().strip():
                self._navigate_history(1)
                return True
            elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
                cursor = self._text_edit.textCursor()
                if not cursor.hasSelection():
                    self.interrupted.emit()
                    return True
        return super().eventFilter(obj, event)

    def _on_send(self):
        text = self._text_edit.toPlainText().strip()
        if text:
            self._history.append(text)
            self._history_idx = -1
            self._text_edit.clear()
            self.submitted.emit(text)

    def _navigate_history(self, direction: int):
        if not self._history:
            return
        if direction == -1:
            if self._history_idx == -1:
                self._current_text = self._text_edit.toPlainText()
                self._history_idx = len(self._history) - 1
            elif self._history_idx > 0:
                self._history_idx -= 1
        else:
            if self._history_idx >= 0:
                self._history_idx += 1
                if self._history_idx >= len(self._history):
                    self._history_idx = -1
                    self._text_edit.setPlainText(self._current_text)
                    return
        if 0 <= self._history_idx < len(self._history):
            self._text_edit.setPlainText(self._history[self._history_idx])

    def set_thinking(self, thinking: bool):
        self._send_btn.setVisible(not thinking)
        self._stop_btn.setVisible(thinking)
        self._text_edit.setReadOnly(thinking)
        if thinking:
            self._text_edit.setStyleSheet(
                "QTextEdit{background:#161b22;border:1px solid #eab308;border-radius:8px;"
                "color:#94a3b8;padding:8px 12px;}"
            )
        else:
            self._text_edit.setStyleSheet(
                "QTextEdit{background:#161b22;border:1px solid #30363d;border-radius:8px;"
                "color:#e6edf3;padding:8px 12px;selection-background-color:#3b82f6;}"
                "QTextEdit:focus{border:1px solid #3b82f6;}"
            )

    def focus_input(self):
        self._text_edit.setFocus()

    def clear(self):
        self._text_edit.clear()
