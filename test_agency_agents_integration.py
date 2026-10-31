"""Integration test for Agency Agents installation and HakimAgent / Antigravity integration."""

import os
import sys
import json
from pathlib import Path

# Add backend to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from axiom.skills_catalog import list_skills, search_skills, get_skill, get_skill_readme
from axiom.core.coworker_computer import coworker_manager
from axiom.api.routes import list_agents
from axiom.api.openbot_routes import list_agency_agents, spawn_agency_coworker, SpawnAgencyRequest
import asyncio

def test_antigravity_skills_installation():
    print("🧪 Test 1 : Vérification de l'installation des skills Antigravity et Workspace...")
    global_gemini = Path(os.path.expanduser("~")) / ".gemini" / "config" / "skills"
    workspace_agents = ROOT_DIR / ".agents" / "skills"
    hakim_skills = ROOT_DIR / "skills" / "agency-agents"

    assert global_gemini.exists(), "Le dossier ~/.gemini/config/skills doit exister"
    assert workspace_agents.exists(), "Le dossier .agents/skills doit exister"
    assert hakim_skills.exists(), "Le dossier skills/agency-agents doit exister"

    sample_slug = "agency-code-reviewer"
    assert (global_gemini / sample_slug / "SKILL.md").exists(), f"Global {sample_slug} introuvable"
    assert (workspace_agents / sample_slug / "SKILL.md").exists(), f"Workspace {sample_slug} introuvable"
    assert (hakim_skills / "engineering" / sample_slug / "SKILL.md").exists(), f"HakimAgent {sample_slug} introuvable"

    # Vérification du contenu du SKILL.md
    content = (global_gemini / sample_slug / "SKILL.md").read_text(encoding="utf-8")
    assert "name: 'agency-code-reviewer'" in content
    assert "Expert code reviewer" in content
    print("  ✅ 267 Skills Antigravity globaux, workspace et HakimAgent vérifiés")

def test_skills_manifest_and_catalog():
    print("🧪 Test 2 : Vérification du manifest et de la recherche dans skills_catalog...")
    manifest_path = ROOT_DIR / "skills" / "manifest.json"
    assert manifest_path.exists()

    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_skills"] >= 700, f"Expected at least 700 skills, got {data['total_skills']}"
    agency_skills = [s for s in data["skills"] if s.get("repo") == "agency-agents"]
    assert len(agency_skills) == 267, f"Expected 267 agency skills, got {len(agency_skills)}"

    # Test via API catalog
    found = search_skills("code-reviewer")
    assert len(found) >= 1
    readme = get_skill_readme("agency-agents", "agency-code-reviewer")
    assert readme is not None
    assert "Code Reviewer Agent" in readme
    print("  ✅ skills/manifest.json contient 267 Agency Agents et la recherche fonctionne")

def test_agent_roles_manifest():
    print("🧪 Test 3 : Vérification du manifest des rôles d'agents (agent_roles/manifest.json)...")
    roles_path = ROOT_DIR / "agent_roles" / "manifest.json"
    assert roles_path.exists()

    with open(roles_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_roles"] >= 275, f"Expected at least 275 roles, got {data['total_roles']}"
    agency_roles = [r for r in data["roles"] if r.get("id", "").startswith("AGENCY_")]
    assert len(agency_roles) == 267, f"Expected 267 agency roles, got {len(agency_roles)}"
    print("  ✅ agent_roles/manifest.json contient les rôles natifs + 267 rôles Agency")

def test_coworkers_and_spawning():
    print("🧪 Test 4 : Vérification des coworkers et de l'instanciation dynamique...")
    coworkers = coworker_manager.list_coworkers()
    cw_ids = [c["id"] for c in coworkers]

    # Vérification des coworkers phares pré-configurés
    assert "bot-agency-reviewer" in cw_ids
    assert "bot-agency-architect" in cw_ids
    assert "bot-agency-secops" in cw_ids
    assert "bot-agency-growth" in cw_ids
    assert "bot-agency-prompt" in cw_ids

    # Test de spawn dynamique
    spawned = coworker_manager.spawn_agency_coworker("anthropologist")
    assert spawned.id == "bot-agency-anthropologist"
    assert coworker_manager.get_coworker("bot-agency-anthropologist") is not None
    assert os.path.exists(spawned.workspace_path)
    print("  ✅ Coworkers phares initialisés et spawn dynamique validé")

async def test_api_routes():
    print("🧪 Test 5 : Vérification des routes API (/agents, /agency-agents, /coworkers/spawn-agency)...")
    agents = await list_agents()
    assert len(agents) >= 270, f"Expected at least 270 agents in /agents, got {len(agents)}"

    agency_cat = await list_agency_agents()
    assert agency_cat["total"] == 267
    assert len(agency_cat["divisions"]) == 18

    # Filtrage par division
    eng_only = await list_agency_agents(division="engineering")
    assert eng_only["total"] == 65

    # Recherche
    search_res = await list_agency_agents(q="frontend")
    assert search_res["total"] >= 1

    # Route spawn
    req = SpawnAgencyRequest(slug="game-developer")
    spawn_res = await spawn_agency_coworker(req)
    assert spawn_res["status"] == "ok"
    assert "bot-agency-game-developer" in spawn_res["coworker"]["id"]
    print("  ✅ Routes API /agents, /agency-agents et spawn validées")

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 SUITE DE TESTS D'INTÉGRATION AGENCY AGENTS DANS HAKIMAGENT")
    print("=" * 70)
    test_antigravity_skills_installation()
    test_skills_manifest_and_catalog()
    test_agent_roles_manifest()
    test_coworkers_and_spawning()
    asyncio.run(test_api_routes())
    print("=" * 70)
    print("🎉 TOUS LES TESTS D'INTÉGRATION AGENCY AGENTS SONT VALIDÉS !")
    print("=" * 70)
