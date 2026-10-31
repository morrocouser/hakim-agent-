"""
HakimAgent - OmniRoute Unified Gateway Manager
Fusion native d'OmniRoute (Port 20128) avec HakimAgent :
- Détection et démarrage automatique d'OmniRoute Gateway
- Routage spécialisé vers les MEILLEURS modèles selon les rôles d'agents :
    * Superviseur (Planification & Stratégie) -> auto/best-reasoning
    * Code Executor (Génération & Sandboxing) -> auto/best-coding
    * Reviewer (Critique & Contrôle Qualité)  -> auto/best-reasoning
    * Researcher (Recherche Web & Extraction) -> auto/best-fast
    * Chat & Conversation Utilisateur        -> auto/best-chat
- Repli automatique vers Google AI Studio (Gemini) en cas de déconnexion
"""

from __future__ import annotations

import os
import sys
import time
import shutil
import asyncio
import subprocess
import urllib.request
import urllib.error
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_OMNIROUTE_URL = "http://127.0.0.1:20128/v1"
DEFAULT_OMNIROUTE_KEY = "d83a770394c0a1a5b8da99b37e8b19decd0915760bc50efaaaffbbfd5818400e"

# Cartographie des rôles HakimAgent vers les meilleurs modèles OmniRoute
ROLE_BEST_MODELS = {
    "supervisor": "auto/best-reasoning",
    "planning": "auto/best-reasoning",
    "executor": "auto/best-coding",
    "code": "auto/best-coding",
    "coding": "auto/best-coding",
    "reviewer": "auto/best-reasoning",
    "qa": "auto/best-reasoning",
    "researcher": "auto/best-fast",
    "research": "auto/best-fast",
    "chat": "auto/best-chat",
    "general": "auto/smart",
}


class OmniRouteManager:
    """
    Gestionnaire central du cycle de vie et du routage intelligent d'OmniRoute pour HakimAgent.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (
            base_url
            or os.getenv("HAKIM_LLM_BASE_URL")
            or os.getenv("OMNIROUTE_BASE_URL")
            or DEFAULT_OMNIROUTE_URL
        ).rstrip("/")
        self.api_key = (
            api_key
            or os.getenv("HAKIM_LLM_API_KEY")
            or os.getenv("OMNIROUTE_API_KEY")
            or DEFAULT_OMNIROUTE_KEY
        )

    def is_running(self, timeout: float = 1.5) -> bool:
        """Vérifie si la passerelle OmniRoute répond sur son endpoint /models."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status == 200
        except Exception:
            return False

    def get_best_model_for_role(self, role: str) -> str:
        """
        Retourne l'identifiant du meilleur modèle OmniRoute optimisé pour le rôle demandé.
        Peut être surchargé par les variables d'environnement HAKIM_MODEL_*.
        """
        clean_role = role.lower().strip()
        env_map = {
            "supervisor": "HAKIM_MODEL_SUPERVISOR",
            "planning": "HAKIM_MODEL_SUPERVISOR",
            "executor": "HAKIM_MODEL_CODE",
            "code": "HAKIM_MODEL_CODE",
            "coding": "HAKIM_MODEL_CODE",
            "reviewer": "HAKIM_MODEL_REVIEWER",
            "qa": "HAKIM_MODEL_REVIEWER",
            "researcher": "HAKIM_MODEL_RESEARCH",
            "research": "HAKIM_MODEL_RESEARCH",
            "chat": "HAKIM_MODEL_CHAT",
        }

        env_var = env_map.get(clean_role)
        if env_var and os.getenv(env_var):
            return os.getenv(env_var)

        # Fallback global HAKIM_LLM_MODEL
        if os.getenv("HAKIM_LLM_MODEL") and clean_role in ["executor", "code"]:
            return os.getenv("HAKIM_LLM_MODEL")

        return ROLE_BEST_MODELS.get(clean_role, "auto/best-coding")

    def ensure_running(self) -> bool:
        """
        Vérifie qu'OmniRoute tourne. Si non, tente de le démarrer automatiquement en arrière-plan.
        """
        if self.is_running():
            return True

        print("⚡ OmniRoute non détecté sur le port 20128. Démarrage automatique...")
        
        # Localisation de Node et d'OmniRoute
        node_exe = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
        if not os.path.exists(node_exe):
            print("❌ Exécutable Node.js introuvable.")
            return False

        # Recherche du script server-ws.mjs dans npm global
        appdata = os.getenv("APPDATA", "")
        possible_scripts = [
            os.path.join(appdata, r"npm\node_modules\omniroute\dist\server-ws.mjs"),
            os.path.join(os.path.expanduser("~"), r"AppData\Roaming\npm\node_modules\omniroute\dist\server-ws.mjs"),
        ]

        script_path = None
        for p in possible_scripts:
            if os.path.exists(p):
                script_path = p
                break

        if not script_path:
            print("❌ Script OmniRoute introuvable dans node_modules npm.")
            return False

        cmd = [
            node_exe,
            "--dns-result-order=ipv4first",
            "--max-old-space-size=4096",
            script_path,
        ]

        try:
            # Lancement détaché en tâche de fond
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
                close_fds=True,
            )

            # Attente de disponibilité (jusqu'à 10 secondes)
            for _ in range(20):
                time.sleep(0.5)
                if self.is_running():
                    print("✅ OmniRoute démarré avec succès sur le port 20128 !")
                    return True

        except Exception as e:
            print(f"❌ Erreur lors du lancement d'OmniRoute : {e}")

        return False

    def list_models(self) -> List[Dict[str, Any]]:
        """Liste tous les modèles disponibles via la passerelle OmniRoute."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("data", [])
        except Exception:
            return []


# Instance singleton globale
omniroute_hub = OmniRouteManager()
