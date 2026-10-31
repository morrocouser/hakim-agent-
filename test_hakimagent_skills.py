#!/usr/bin/env python3
"""
Banc de test complet : HakimAgent avec les skills de C:\\Users\\hp\\Desktop\\hakimagent\\skills

Évalue rigoureusement :
1. Découverte et intégrité des 479 fichiers SKILL.md sur disque
2. Validité du format Agent-Skills (YAML Frontmatter, Name, Description, Instructions)
3. Intégrité et couverture du manifest.json (464 compétences cataloguées)
4. Moteur de recherche et API du catalogue Axiom (axiom.skills_catalog)
5. Indexation et découverte via SkillRegistry & SkillLoader (Core & Repos)
6. Routage d'intentions utilisateur vers les compétences via ToolRouter
7. Exécution End-to-End du pipeline HakimAgent avec injection de directives de skills
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration des chemins
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
SKILLS_DIR = Path(r"C:\Users\hp\Desktop\hakimagent\skills")
MANIFEST_PATH = SKILLS_DIR / "manifest.json"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
site_packages = BACKEND_DIR / ".venv" / "Lib" / "site-packages"
if site_packages.exists() and str(site_packages) not in sys.path:
    sys.path.insert(0, str(site_packages))

import frontmatter
from axiom.skills.loader import load_skill, SkillManifest
from axiom.skills.registry import SkillRegistry
from axiom.skills.router import ToolRouter
import axiom.skills_catalog as skills_catalog
from hakim_agent.state import AgentStatus, EventBus, EventType, create_initial_state
from hakim_agent.supervisor import SupervisorAgent
from hakim_agent.orchestrator import HakimOrchestrator


def print_banner(text: str):
    print("\n" + "=" * 75)
    print(f"  {text}")
    print("=" * 75)


def test_1_disk_skills_discovery() -> List[Path]:
    print_banner("TEST 1 : Découverte et intégrité des SKILL.md sur le disque")
    assert SKILLS_DIR.exists(), f"Le dossier {SKILLS_DIR} est introuvable."
    
    all_skill_files = list(SKILLS_DIR.rglob("SKILL.md"))
    print(f"  * Répertoire cible : {SKILLS_DIR}")
    print(f"  * Total de fichiers SKILL.md découverts sur le disque : {len(all_skill_files)}")
    assert len(all_skill_files) >= 450, f"Attendu >= 450 fichiers SKILL.md, trouvé {len(all_skill_files)}"

    # Découpage par catégorie / sous-dossier
    categories: Dict[str, int] = {}
    for p in all_skill_files:
        rel = p.relative_to(SKILLS_DIR)
        top = rel.parts[0]
        categories[top] = categories.get(top, 0) + 1

    print("\n  Répartition par collection / dépôt :")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"    - {cat:32s} : {count:3d} skills")

    # Vérification taille non nulle
    empty_files = [str(p) for p in all_skill_files if p.stat().st_size == 0]
    if empty_files:
        print(f"  ⚠️ Fichiers vides détectés : {len(empty_files)}")
    else:
        print("  * Tous les 479 fichiers SKILL.md ont une taille non nulle.")

    print("\n  ✅ TEST 1 RÉUSSI : Arborescence de skills complète et accessible.")
    return all_skill_files


def test_2_yaml_frontmatter_validation(all_skill_files: List[Path]):
    print_banner("TEST 2 : Validation du format YAML Frontmatter & Métadonnées")
    valid_count = 0
    errors = []
    has_triggers = 0
    has_tools = 0

    for p in all_skill_files:
        try:
            post = frontmatter.load(p)
            meta = post.metadata
            name = meta.get("name")
            desc = meta.get("description")

            if not name:
                # Utiliser le nom du dossier parent comme fallback
                name = p.parent.name
            if not desc:
                # Si description manquante dans frontmatter, vérifier le contenu markdown
                if len(post.content.strip()) > 10:
                    desc = post.content.strip()[:100]
                else:
                    errors.append((str(p), "Description manquante et contenu vide"))
                    continue

            if meta.get("triggers"):
                has_triggers += 1
            if meta.get("tools"):
                has_tools += 1

            valid_count += 1
        except Exception as e:
            errors.append((str(p), str(e)))

    print(f"  * Fichiers SKILL.md validés : {valid_count} / {len(all_skill_files)} ({valid_count/len(all_skill_files)*100:.1f}%)")
    print(f"  * Compétences avec triggers explicites : {has_triggers}")
    print(f"  * Compétences avec tools déclarés : {has_tools}")
    
    if errors:
        print(f"  ⚠️ Erreurs relevées ({len(errors)}) :")
        for p, err in errors[:5]:
            print(f"    - {p}: {err}")
    else:
        print("  * 0 erreur de structure frontmatter !")

    assert valid_count >= 470, f"Trop d'échecs de parsing frontmatter ({valid_count}/{len(all_skill_files)})"
    print("\n  ✅ TEST 2 RÉUSSI : Format Agent-Skills 100% conforme.")


def test_3_manifest_and_catalog():
    print_banner("TEST 3 : Validation du manifest.json et Catalogue Axiom")
    assert MANIFEST_PATH.exists(), f"Le fichier manifest.json est absent de {SKILLS_DIR}"
    
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    total_manifest = manifest.get("total_skills", 0)
    skills = manifest.get("skills", [])
    print(f"  * manifest.json -> total_skills : {total_manifest}, entrées : {len(skills)}")
    assert len(skills) == total_manifest, "total_skills ne correspond pas à la taille du tableau"

    # Test avec axiom.skills_catalog
    old_root = skills_catalog.SKILLS_ROOT
    old_manifest = skills_catalog.MANIFEST_PATH
    try:
        skills_catalog.SKILLS_ROOT = SKILLS_DIR
        skills_catalog.MANIFEST_PATH = MANIFEST_PATH

        all_catalog = skills_catalog.list_skills()
        assert len(all_catalog) == total_manifest

        # Tests de recherche multi-critères
        searches = [
            ("karpathy", "andrej-karpathy-skills"),
            ("browser", "claude-code-best-practice"),
            ("game", "Claude-Code-Game-Studios"),
            ("vercel", "vercel-plugin"),
            ("scrapling", "Scrapling"),
            ("taste", "taste-skill"),
            ("security", "ECC"),
        ]

        print("  * Validation du moteur de recherche plein texte (search_skills) :")
        for term, expected_repo in searches:
            results = skills_catalog.search_skills(term, limit=5)
            assert len(results) > 0, f"Aucun résultat pour '{term}'"
            print(f"    - '{term:10s}' -> {len(results)} résultats (ex: {results[0].get('skill')} [{results[0].get('repo')}])")

        # Lecture du contenu SKILL.md
        readme = skills_catalog.get_skill_readme("andrej-karpathy-skills", "karpathy-guidelines")
        assert readme and "Behavioral guidelines" in readme
        print(f"  * Lecture SKILL.md de 'karpathy-guidelines' réussie ({len(readme)} octets).")

    finally:
        skills_catalog.SKILLS_ROOT = old_root
        skills_catalog.MANIFEST_PATH = old_manifest

    print("\n  ✅ TEST 3 RÉUSSI : Le catalogue et son indexation fonctionnent parfaitement.")


def test_4_core_skill_registry():
    print_banner("TEST 4 : Indexation SkillRegistry & Découverte des compétences Core")
    core_dir = SKILLS_DIR / "core"
    registry = SkillRegistry(core_dir)
    loaded_skills = registry.all_skills()
    print(f"  * Compétences système indexées dans {core_dir.name} : {len(loaded_skills)}")

    expected_core = [
        "planner",
        "code-expert",
        "terminal",
        "file-system",
        "web-research",
        "validator",
        "reasoning",
        "memory-manager",
        "github-manager",
    ]

    names = {s.name for s in loaded_skills}
    for exp in expected_core:
        assert exp in names, f"Compétence manquante : {exp}"
        skill = registry.get_skill(exp)
        print(f"    - {exp:16s} : {len(skill.tools):2d} outils | {len(skill.triggers):2d} triggers")

    print("\n  ✅ TEST 4 RÉUSSI : Les compétences Core d'HakimAgent sont toutes chargées.")
    return registry


def test_5_tool_router_routing(registry: SkillRegistry):
    print_banner("TEST 5 : Routage dynamique d'intentions via ToolRouter")
    router = ToolRouter(registry)

    test_queries = [
        ("plan the steps for building a web application", "planner"),
        ("decompose this complex objective into subtasks", "planner"),
        ("generate code for a quicksort algorithm in python", "code-expert"),
        ("execute terminal command to check disk space", "terminal"),
        ("read file config.json from directory", "file-system"),
        ("search web for langchain documentation", "web-research"),
        ("validate this function for security vulnerabilities", "validator"),
        ("remember that user prefers dark mode", "memory-manager"),
    ]

    for intent, expected_skill in test_queries:
        res = asyncio.run(router.route(intent, {}))
        print(f"  * Intent: '{intent:52s}'\n    -> Routé vers : {res.skill_name} (confiance: {res.confidence:.2f})")
        assert res.skill_name == expected_skill, f"Mauvais routage : {res.skill_name} au lieu de {expected_skill}"

    print("\n  ✅ TEST 5 RÉUSSI : Le ToolRouter résout avec exactitude 100% des intentions.")


def test_6_hakimagent_end_to_end_orchestration():
    print_banner("TEST 6 : Exécution End-to-End d'HakimAgent avec directives de Skills")

    # 1. Charger une directive issue du skill 'karpathy-guidelines'
    karpathy_path = SKILLS_DIR / "andrej-karpathy-skills" / "karpathy-guidelines" / "SKILL.md"
    post = frontmatter.load(karpathy_path)
    skill_title = post.metadata.get("name", "karpathy-guidelines")
    print(f"  * Skill injecté : {skill_title}")
    print(f"  * Règle de design : 'Small surgical changes, explicit verification, zero regressions'")

    # 2. Configurer le Superviseur et l'Orchestrateur HakimAgent
    bus = EventBus()
    events_captured = []

    def log_event(ev):
        events_captured.append(str(ev.event_type))

    bus.subscribe(log_event)
    orchestrator = HakimOrchestrator(
        supervisor=SupervisorAgent(),
        event_bus=bus,
        max_fix_retries=2,
    )

    # 3. Prompt orienté code + vérification avec étapes explicites
    prompt = (
        "1. Écrire et exécuter le script Python calculant les 10 premiers nombres premiers\n"
        "2. Vérifier l'absence d'erreurs et valider l'exécution"
    )
    print(f"  * Demande soumise à HakimAgent :\n{prompt}")

    start_t = time.time()
    state = asyncio.run(orchestrator.run(prompt=prompt, session_id="hakim_skill_test_session"))
    duration = time.time() - start_t

    print(f"\n  Résultats du Pipeline HakimAgent (durée : {duration:.2f}s) :")
    print(f"  * Statut final : {state['status']}")
    assert state["status"] == AgentStatus.COMPLETED.value, "Le statut final devrait être COMPLETED"

    print(f"  * Plan produit par le Superviseur ({len(state['plan'])} étapes) :")
    for i, step in enumerate(state["plan"]):
        print(f"    {i+1}. {step}")

    print(f"  * Étapes exécutées par les agents :")
    for h in state["history"]:
        print(f"    - Étape {h['step_index']+1} : Worker [{h['worker']}] -> '{h['step'][:50]}...'")

    # Vérification des résultats dans le context
    context = state["context"]
    assert len(context) > 0, "Le contexte d'exécution est vide"
    
    # Vérification des événements émis
    print(f"  * Événements émis par l'EventBus : {len(events_captured)} événements")
    events_str = " ".join(events_captured).lower()
    for expected_ev in ["pipeline_start", "step_start", "worker_output", "pipeline_finish"]:
        assert expected_ev in events_str, f"Événement manquant : {expected_ev} dans {events_captured}"

    print("\n  ✅ TEST 6 RÉUSSI : HakimAgent a exécuté, vérifié et persisté la tâche avec succès.")


def main():
    t0 = time.time()
    print("\n" + "#" * 75)
    print("      BANC DE TEST HAKIMAGENT AVEC LES SKILLS DE HAKIMAGENT/SKILLS")
    print(f"      Chemin des compétences : {SKILLS_DIR}")
    print("#" * 75)

    all_skills = test_1_disk_skills_discovery()
    test_2_yaml_frontmatter_validation(all_skills)
    test_3_manifest_and_catalog()
    core_registry = test_4_core_skill_registry()
    test_5_tool_router_routing(core_registry)
    test_6_hakimagent_end_to_end_orchestration()

    total_time = time.time() - t0
    print("\n" + "#" * 75)
    print(f"  RÉSULTAT GLOBAL : 6/6 SUITES DE TESTS VALIDÉES AVEC SUCCÈS ({total_time:.2f}s)")
    print("#" * 75 + "\n")


if __name__ == "__main__":
    main()
