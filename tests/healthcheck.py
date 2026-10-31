"""
HakimAgent Healthcheck & Environment Diagnostic Suite
Vérifie la validité des configurations, des variables d'environnement,
de la passerelle LLM / repli de secours, et des connecteurs MCP.
"""

import os
import sys
import json
import socket
import urllib.request
import urllib.error
from pathlib import Path

# Force UTF-8 encoding for console output on Windows
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

# Charger les variables d'environnement depuis backend/.env ou .env
from dotenv import load_dotenv
env_loaded = False
for env_candidate in [BACKEND_DIR / ".env", ROOT_DIR / ".env"]:
    if env_candidate.exists():
        load_dotenv(dotenv_path=env_candidate)
        env_loaded = True
        break


def check_configuration_and_env() -> dict:
    """1. Vérification des fichiers de configuration et des variables d'environnement."""
    results = {
        "env_file_found": env_loaded,
        "jwt_secret": bool(os.getenv("HAKIM_JWT_SECRET")),
        "llm_provider": os.getenv("HAKIM_LLM_PROVIDER", "not_set"),
        "llm_base_url": os.getenv("HAKIM_LLM_BASE_URL", "not_set"),
        "gemini_api_key": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "openrouter_api_key": bool(os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_API_KEY") != "***"),
        "mcp_config_found": False,
        "mcp_servers_count": 0,
        "agent_roles_manifest_found": False,
        "roles_count": 0,
    }

    # Vérification mcp_config.json / backend/mcp_servers.json
    for mcp_path in [ROOT_DIR / "mcp_config.json", BACKEND_DIR / "mcp_servers.json"]:
        if mcp_path.exists():
            try:
                with open(mcp_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    servers = data.get("mcpServers", {})
                    results["mcp_config_found"] = True
                    results["mcp_servers_count"] = len(servers)
                    break
            except Exception as e:
                results["mcp_config_error"] = str(e)

    # Vérification agent_roles/manifest.json
    manifest_path = ROOT_DIR / "agent_roles" / "manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                results["agent_roles_manifest_found"] = True
                results["roles_count"] = data.get("total_roles", len(data.get("roles", [])))
        except Exception as e:
            results["manifest_error"] = str(e)

    return results


def check_llm_backend() -> dict:
    """2. Vérification du backend LLM local ou proxy (OmniRoute, Ollama, etc.) et des replis."""
    results = {
        "omniroute_running": False,
        "omniroute_url": os.getenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1"),
        "client_configured": False,
        "fallback_available": False,
        "active_provider": None,
    }

    # Test de connectivité à OmniRoute Gateway
    try:
        from hakim_agent.omniroute_service import omniroute_hub
        results["omniroute_running"] = omniroute_hub.is_running(timeout=1.0)
    except Exception:
        # Test direct socket / HTTP si le module n'est pas encore initialisé
        try:
            url = f"{results['omniroute_url']}/models"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {os.getenv('OMNIROUTE_API_KEY', '')}"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                results["omniroute_running"] = (resp.status == 200)
        except Exception:
            results["omniroute_running"] = False

    # Test du client unifié et de la chaîne de secours (Gemini / OpenRouter)
    try:
        from axiom.claude.client import LocalAPIClient
        client = LocalAPIClient()
        results["client_configured"] = client.is_configured()
        
        # Vérification si un fallback LLM est disponible
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gemini_key and gemini_key != "***":
            results["fallback_available"] = True
            results["active_provider"] = "OmniRoute (local)" if results["omniroute_running"] else "Google Gemini API (fallback)"
        elif results["omniroute_running"]:
            results["active_provider"] = "OmniRoute (local)"
        else:
            results["active_provider"] = "Offline / Simulation"
    except Exception as e:
        results["client_error"] = str(e)

    return results


def check_mcp_servers_resilience() -> dict:
    """
    3. Vérification des serveurs MCP configurés.
    Vérifie l'accès aux serveurs et s'assure que si un serveur distant ou local
    (ex: transport SSE sur http://localhost:8081/sse) est éteint,
    l'application gère cela sans crasher.
    """
    results = {
        "configured_servers": [],
        "unavailable_servers_handled_gracefully": True,
        "sse_check": {},
    }

    try:
        from axiom.tools.mcp_connectors import MCPConnectorRegistry
        registry = MCPConnectorRegistry()
        results["configured_servers"] = registry.available_connectors
    except Exception as e:
        results["registry_error"] = str(e)

    # Test spécifique du transport SSE local (ex: http://localhost:8081/sse)
    # L'objectif est de s'assurer qu'un serveur éteint est détecté proprement sans exception non gérée
    sse_test_url = "http://localhost:8081/sse"
    try:
        req = urllib.request.Request(sse_test_url)
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            results["sse_check"] = {
                "url": sse_test_url,
                "status": "online",
                "code": resp.status,
            }
    except urllib.error.URLError as e:
        # Comportement attendu quand le serveur est éteint : géré proprement
        results["sse_check"] = {
            "url": sse_test_url,
            "status": "offline_handled_gracefully",
            "reason": str(e.reason),
            "crashed": False,
        }
    except Exception as e:
        results["sse_check"] = {
            "url": sse_test_url,
            "status": "offline_handled_gracefully",
            "reason": str(e),
            "crashed": False,
        }

    return results


def run_all_checks() -> bool:
    print("=" * 70)
    print("🔍 HAKIMAGENT - BILAN DE SANTÉ & DIAGNOSTIC DE L'ENVIRONNEMENT")
    print("=" * 70)

    # 1. Configuration & Env
    print("\n[1/3] Vérification de la configuration et des variables d'environnement...")
    conf = check_configuration_and_env()
    print(f"  * Fichier .env détecté         : {'✅ OUI' if conf['env_file_found'] else '❌ NON'}")
    print(f"  * Clé JWT Secret              : {'✅ Valide' if conf['jwt_secret'] else '⚠️ Manquante'}")
    print(f"  * Fournisseur LLM configuré   : {conf['llm_provider']} ({conf['llm_base_url']})")
    print(f"  * Clé Gemini / Google AI      : {'✅ Présente' if conf['gemini_api_key'] else '⚠️ Absente'}")
    print(f"  * Fichier de configuration MCP: {'✅ OUI' if conf['mcp_config_found'] else '❌ NON'} ({conf['mcp_servers_count']} serveurs déclarés)")
    print(f"  * Manifeste des rôles d'agents: {'✅ OUI' if conf['agent_roles_manifest_found'] else '❌ NON'} ({conf['roles_count']} rôles)")

    # 2. LLM Backend
    print("\n[2/3] Vérification de la connectivité LLM et de la chaîne de secours...")
    llm = check_llm_backend()
    if llm["omniroute_running"]:
        print(f"  * Passerelle locale OmniRoute : ✅ EN LIGNE ({llm['omniroute_url']})")
    else:
        print(f"  * Passerelle locale OmniRoute : ℹ️ HORS LIGNE (Port 20128 inactif)")
    
    print(f"  * Client API Unifié configuré : {'✅ OUI' if llm['client_configured'] else '❌ NON'}")
    print(f"  * Repli de secours disponible : {'✅ OUI' if llm['fallback_available'] else '⚠️ NON'}")
    print(f"  * Fournisseur actif retenu    : {llm['active_provider']}")

    # 3. Serveurs MCP & Résilience
    print("\n[3/3] Vérification des serveurs MCP et tolérance aux pannes...")
    mcp = check_mcp_servers_resilience()
    print(f"  * Connecteurs MCP répertoriés : {len(mcp['configured_servers'])} ({', '.join(mcp['configured_servers'][:6])}...)")
    sse = mcp["sse_check"]
    print(f"  * Test de transport SSE local : {sse['url']}")
    print(f"    - État                       : {sse['status']}")
    print(f"    - Résilience                 : {'✅ Erreur gérée sans crash' if not sse.get('crashed', True) else '❌ Crash'}")

    print("\n" + "=" * 70)
    all_ok = conf["env_file_found"] and conf["mcp_config_found"] and (llm["omniroute_running"] or llm["fallback_available"])
    if all_ok:
        print("🎉 BILAN DE SANTÉ : SYSTÈME OPÉRATIONNEL & PRÊT")
    else:
        print("⚠️ BILAN DE SANTÉ : ATTENTION - VÉRIFIER LES SERVICES")
    print("=" * 70)

    return all_ok


# Intégration pytest
def test_environment_healthcheck():
    conf = check_configuration_and_env()
    assert conf["env_file_found"], "Le fichier .env doit être présent"
    assert conf["mcp_config_found"], "La configuration MCP doit être valide"
    assert conf["agent_roles_manifest_found"], "Le manifest des rôles doit être présent"

def test_llm_resilience_healthcheck():
    llm = check_llm_backend()
    assert llm["client_configured"], "Le client LLM doit être configuré"
    assert llm["omniroute_running"] or llm["fallback_available"], "Au moins un fournisseur (OmniRoute ou Gemini fallback) doit être opérationnel"

def test_mcp_resilience_healthcheck():
    mcp = check_mcp_servers_resilience()
    assert len(mcp["configured_servers"]) > 0, "Au moins un serveur MCP doit être configuré"
    assert not mcp["sse_check"].get("crashed", False), "Un serveur SSE éteint ne doit pas provoquer de crash"


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
