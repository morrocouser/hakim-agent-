import sys
import os

# Ensure backend is on path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from desktop.main_window import MainWindow


def load_stylesheet():
    qss_path = os.path.join(os.path.dirname(__file__), "resources", "axiom.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("APEX")
    app.setApplicationVersion("4.0.0")
    app.setOrganizationName("APEX")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
