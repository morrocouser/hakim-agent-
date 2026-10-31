"""
HakimAgent - Tests de l'Interface Graphique Desktop et WebUI (PySide6 & FastAPI)
Valide l'initialisation de l'application de bureau en mode offscreen (sans affichage physique bloquant)
et le montage de l'interface WebUI statique Next.js.
"""

import os
import sys
import pytest
from pathlib import Path

# Force l'encodage UTF-8 sous Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Configuration mode offscreen pour Qt (headless CI/test)
os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_desktop_main_window_headless():
    """Vérifie que la fenêtre PySide6 principale démarre et initialise tous ses composants sans crash."""
    from PySide6.QtWidgets import QApplication
    from desktop.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window is not None
    assert "APEX" in window.windowTitle() or "Orchestrateur" in window.windowTitle()
    
    # Vérification des sous-widgets principaux
    assert hasattr(window, "_chat_area") and window._chat_area is not None
    assert hasattr(window, "_input") and window._input is not None
    assert hasattr(window, "_agent_dock") and window._agent_dock is not None

    widgets = window.findChildren(object)
    assert len(widgets) > 20, f"Attendu > 20 sous-composants Qt, trouvé {len(widgets)}"
    print(f"\n  ✅ Interface Desktop PySide6 validée ({len(widgets)} composants initialisés en mode offscreen)")


def test_desktop_web_app_mounting():
    """Vérifie la détection et le montage du build Next.js (frontend/out) sur FastAPI."""
    from desktop.web_app import find_build_dir, _mount_webui
    from starlette.testclient import TestClient
    from axiom.api.main import app

    build_dir = find_build_dir()
    assert build_dir is not None, "Le dossier frontend/out doit exister"
    assert build_dir.is_dir()

    # Montage de la WebUI
    _mount_webui(build_dir)

    with TestClient(app) as client:
        # La racine doit désormais servir le HTML du frontend
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        # Vérifie la présence de balises standard HTML
        assert "<html" in resp.text.lower() or "<!doctype" in resp.text.lower()
    print("  ✅ Montage WebUI Next.js validé (route racine sert l'interface HTML)")


if __name__ == "__main__":
    print("=" * 70)
    print("🖥️ TESTS DE L'INTERFACE GRAPHIQUE DESKTOP & WEBUI")
    print("=" * 70)
    test_desktop_main_window_headless()
    test_desktop_web_app_mounting()
    print("=" * 70)
    print("🎉 TOUS LES TESTS DE L'INTERFACE DESKTOP SONT VALIDÉS !")
    print("=" * 70)
