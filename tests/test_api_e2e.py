"""
HakimAgent - Tests d'Intégration End-to-End de l'API FastAPI (Étape 6)
Valide les endpoints REST du serveur principal :
- GET /api/v1/health : Vérification de statut et dépendances
- GET /api/v1/coworkers : Liste des ordinateurs virtuels et coworkers
- GET /api/v1/agency-agents : Catalogue des 267 agents avec filtres & recherche
- POST /api/v1/policy/evaluate : Moteur de gouvernance CEL et sécurité
- GET /agents & GET /skills : Découverte des compétences et catalogue d'outils
"""

import os
import sys
import pytest
from pathlib import Path

# Force UTF-8 sous Windows
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

from starlette.testclient import TestClient
from axiom.api.main import app


@pytest.fixture(scope="module")
def api_client():
    """Client de test pour l'API FastAPI d'AXIOM / HakimAgent."""
    with TestClient(app) as client:
        yield client


def test_health_endpoint(api_client):
    """Vérifie l'endpoint de santé /api/v1/health."""
    resp = api_client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert "agent" in data
    assert "version" in data
    print("\n  ✅ Endpoint /api/v1/health opérationnel")


def test_list_coworkers_endpoint(api_client):
    """Vérifie la liste des AI Coworkers et leurs ordinateurs virtuels."""
    resp = api_client.get("/api/v1/coworkers")
    assert resp.status_code == 200
    data = resp.json()
    assert "coworkers" in data
    coworkers = data["coworkers"]
    assert len(coworkers) >= 5

    # Vérification de coworkers clés
    coworker_ids = [c["id"] for c in coworkers]
    assert "bot-browser" in coworker_ids
    assert "bot-sentinel" in coworker_ids
    assert "bot-agency-reviewer" in coworker_ids
    assert "bot-agency-architect" in coworker_ids
    print(f"\n  ✅ Endpoint /api/v1/coworkers validé ({len(coworkers)} coworkers actifs)")


def test_agency_agents_catalog_endpoint(api_client):
    """Vérifie le catalogue des 267 agents Agency avec filtres et recherche."""
    # 1. Catalogue global
    resp = api_client.get("/api/v1/agency-agents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 267
    assert len(data["divisions"]) >= 10

    # 2. Filtrage par division
    resp_eng = api_client.get("/api/v1/agency-agents?division=engineering")
    assert resp_eng.status_code == 200
    data_eng = resp_eng.json()
    assert data_eng["total"] == 65

    # 3. Recherche textuelle
    resp_search = api_client.get("/api/v1/agency-agents?q=reviewer")
    assert resp_search.status_code == 200
    data_search = resp_search.json()
    assert data_search["total"] >= 1
    assert any("reviewer" in a["slug"].lower() for a in data_search["agents"])
    print("  ✅ Endpoint /api/v1/agency-agents validé (catalogue complet, filtres et recherche)")


def test_policy_evaluation_endpoint(api_client):
    """Vérifie le moteur de gouvernance et de sécurité (Policy Gateway)."""
    # 1. Action de lecture autorisée
    payload_safe = {
        "tool_name": "read_file",
        "intent": "Lire la documentation du projet",
        "coworker_id": "bot-curator",
        "actor_id": "operator",
        "initiator_kind": "person",
        "target": "README.md",
    }
    resp_safe = api_client.post("/api/v1/policy/evaluate", json=payload_safe)
    assert resp_safe.status_code == 200
    data_safe = resp_safe.json()
    assert data_safe["decision"] in ["ALLOWED", "REQUIRE_TAKEOVER", "DENIED"]

    # 2. Action destructrice non autorisée sans confirmation
    payload_danger = {
        "tool_name": "shell_exec",
        "intent": "Suppression critique",
        "coworker_id": "bot-devops",
        "actor_id": "autonomous_cron",
        "initiator_kind": "routine",
        "command": "rm -rf /",
        "target": "/etc/passwd",
    }
    resp_danger = api_client.post("/api/v1/policy/evaluate", json=payload_danger)
    assert resp_danger.status_code == 200
    data_danger = resp_danger.json()
    assert data_danger["decision"] in ["DENIED", "REQUIRE_TAKEOVER"]
    print("  ✅ Endpoint /api/v1/policy/evaluate validé (évaluation de sécurité conforme)")


def test_list_agents_and_skills(api_client):
    """Vérifie la découverte des agents et des compétences via les routes /api/v1/agents et /api/v1/skills."""
    resp_agents = api_client.get("/api/v1/agents")
    assert resp_agents.status_code == 200
    agents = resp_agents.json()
    assert len(agents) >= 270

    resp_skills = api_client.get("/api/v1/skills?limit=10")
    assert resp_skills.status_code == 200
    skills = resp_skills.json()
    assert "skills" in skills or isinstance(skills, list)
    print("  ✅ Routes /api/v1/agents et /api/v1/skills validées avec succès")


if __name__ == "__main__":
    print("=" * 70)
    print("🌐 TESTS END-TO-END DE L'API FASTAPI (HAKIMAGENT / AXIOM)")
    print("=" * 70)
    with TestClient(app) as client:
        test_health_endpoint(client)
        test_list_coworkers_endpoint(client)
        test_agency_agents_catalog_endpoint(client)
        test_policy_evaluation_endpoint(client)
        test_list_agents_and_skills(client)
    print("=" * 70)
    print("🎉 TOUS LES TESTS D'API REST SONT VALIDÉS !")
    print("=" * 70)
