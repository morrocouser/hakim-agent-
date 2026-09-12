import os
import threading
import time
from pathlib import Path

import httpx
from fastapi.staticfiles import StaticFiles
from uvicorn import Config, Server

from axiom.api.main import app as api_app

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
RETRY_ATTEMPTS = 10
RETRY_DELAY = 1.0

_WEBUI_MOUNTED = False


def find_build_dir() -> Path | None:
    """Résout le dossier du build statique frontend (frontend/out sous la racine du repo)."""
    override = os.environ.get("AXIOM_WEB_BUILD")
    if override:
        p = Path(override)
        return p if p.is_dir() else None
    repo_root = Path(__file__).resolve().parents[2]
    out = repo_root / "frontend" / "out"
    return out if out.is_dir() else None


def detect_axiom(host: str, port: int, timeout: float = 2.0) -> bool:
    """Vérifie qu'un serveur AXIOM répond déjà sur host:port."""
    try:
        r = httpx.get(f"http://{host}:{port}/api/v1/health", timeout=timeout)
        return r.json().get("agent") == "APEX"
    except Exception:
        return False


def serves_webui(host: str, port: int, timeout: float = 2.0) -> bool:
    """Vérifie que la racine '/' du serveur répond du HTML (frontend monté)."""
    try:
        r = httpx.get(f"http://{host}:{port}/", timeout=timeout)
        return "text/html" in r.headers.get("content-type", "")
    except Exception:
        return False


def _mount_webui(build_dir: Path) -> None:
    """Monte le build statique à la racine '/' de l'app FastAPI, une seule fois."""
    global _WEBUI_MOUNTED
    if _WEBUI_MOUNTED:
        return
    # Retire la route racine JSON existante pour que '/' serve le frontend
    api_app.routes[:] = [
        r for r in api_app.routes if not (getattr(r, "path", None) == "/")
    ]
    api_app.mount("/", StaticFiles(directory=str(build_dir), html=True), name="webui")
    _WEBUI_MOUNTED = True


def _run_server(config: Config) -> None:
    Server(config).run()


def ensure_backend(port: int = DEFAULT_PORT, build_dir: Path | None = None) -> tuple[bool, str]:
    """Garantit un backend AXIOM joignable sur host:port.
    Si un serveur AXIOM répond déjà et sert le frontend (HTML à '/') -> réutilisation.
    Sinon démarre uvicorn dans un thread daemon (et monte le build statique si fourni).
    Retourne (True, url) ou (False, message d'erreur).
    """
    if detect_axiom(HOST, port):
        if serves_webui(HOST, port):
            return True, f"http://{HOST}:{port}"
        return False, (
            f"Un serveur APEX sans interface web tourne déjà sur le port {port}. "
            "Arrêtez-le (ex. Stop-Process) puis réessayez."
        )

    if build_dir is not None and build_dir.is_dir():
        try:
            _mount_webui(build_dir)
        except Exception as e:
            return False, f"Impossible de monter le frontend : {e}"

    config = Config("axiom.api.main:app", host=HOST, port=port, log_level="warning")
    thread = threading.Thread(target=_run_server, args=(config,), daemon=True)
    try:
        thread.start()
    except Exception as e:
        return False, f"Impossible de démarrer le serveur : {e}"

    for _ in range(RETRY_ATTEMPTS):
        if detect_axiom(HOST, port):
            return True, f"http://{HOST}:{port}"
        time.sleep(RETRY_DELAY)
    return False, "Le serveur n'a pas démarré correctement (port occupé ?)."


import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget


class WebAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("APEX")
        self.resize(1280, 800)
        icon_path = Path(__file__).parent / "resources" / "apex-icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self._dev_mode = os.environ.get("AXIOM_DEV") == "1"
        self._error_box = None
        self.browser = None
        self.retry_button = None
        self._central = QWidget()
        self.setCentralWidget(self._central)
        self._retry()

    # ---- Gestion des erreurs ----

    def _show_error(self, title: str, message: str) -> None:
        if self.browser is not None:
            self.browser.deleteLater()
            self.browser = None
        if self._error_box is None:
            layout = QVBoxLayout(self._central)
            label = QLabel(title)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 22px; font-weight: bold; padding: 16px;")
            detail = QLabel(message)
            detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
            detail.setWordWrap(True)
            detail.setStyleSheet("font-size: 13px; color: #888; padding: 0 32px 16px;")
            self.retry_button = QPushButton("Réessayer")
            self.retry_button.clicked.connect(self._retry)
            layout.addStretch()
            layout.addWidget(label)
            layout.addWidget(detail)
            layout.addWidget(self.retry_button)
            layout.addStretch()
            self._error_box = layout
        title_label = self._error_box.itemAt(1).widget()
        detail_label = self._error_box.itemAt(2).widget()
        title_label.setText(title)
        detail_label.setText(message)
        self._error_box.itemAt(3).widget().show()

    def _show_browser(self, url: str) -> None:
        if self._error_box is not None:
            for i in range(self._error_box.count()):
                self._error_box.itemAt(i).widget().hide()
        if self.browser is None:
            self.browser = QWebEngineView(self._central)
            layout = QHBoxLayout(self._central)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.browser)
            self.browser.loadProgress.connect(self._on_progress)
            self.browser.loadFinished.connect(self._on_loaded)
        self.browser.load(QUrl(url))

    def _on_progress(self, progress: int) -> None:
        if progress < 100:
            self.setWindowTitle(f"APEX — chargement {progress}%")

    def _on_loaded(self, ok: bool) -> None:
        self.setWindowTitle("APEX")

    # ---- Démarrage ----

    def _retry(self) -> None:
        try:
            if self._dev_mode:
                self._show_browser("http://localhost:3000")
                return
            build_dir = find_build_dir()
            if build_dir is None:
                self._show_error(
                    "Build introuvable",
                    "Le frontend n'est pas compilé.\nLancez `npm run build` dans le dossier frontend/.",
                )
                return
            ok, result = ensure_backend(DEFAULT_PORT, build_dir)
            if ok:
                self._show_browser(result)
            else:
                self._show_error("Démarrage impossible", result)
        except Exception as e:
            self._show_error("Erreur inattendue", str(e))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("APEX")
    app.setApplicationVersion("4.0.0")
    app.setOrganizationName("APEX")
    icon_path = Path(__file__).parent / "resources" / "apex-icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = WebAppWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
