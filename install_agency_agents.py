#!/usr/bin/env python3
"""
Install Agency Agents (https://github.com/msitarzewski/agency-agents.git) into:
1. Global Antigravity skills directory (~/.gemini/config/skills/agency-<slug>/SKILL.md)
2. Workspace Antigravity skills directory (.agents/skills/agency-<slug>/SKILL.md)
3. HakimAgent skills directory (skills/agency-agents/<division>/agency-<slug>/SKILL.md)
4. HakimAgent skills manifest (skills/manifest.json)
5. HakimAgent agent roles manifest (agent_roles/manifest.json)
"""

import os
import sys
import re
import json
import yaml
import shutil
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
SCRATCH_AGENTS_DIR = PROJECT_ROOT / "scratch" / "agency-agents"
GLOBAL_GEMINI_SKILLS = Path(os.path.expanduser("~")) / ".gemini" / "config" / "skills"
WORKSPACE_AGENTS_SKILLS = PROJECT_ROOT / ".agents" / "skills"
HAKIM_SKILLS_DIR = PROJECT_ROOT / "skills" / "agency-agents"
HAKIM_SKILLS_MANIFEST = PROJECT_ROOT / "skills" / "manifest.json"
HAKIM_ROLES_MANIFEST = PROJECT_ROOT / "agent_roles" / "manifest.json"

DIVISIONS_FILE = SCRATCH_AGENTS_DIR / "divisions.json"

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text

def yaml_quote(text: str) -> str:
    escaped = text.replace("'", "''")
    return f"'{escaped}'"

def main():
    print("=" * 70)
    print("  INSTALLATION DES AGENCY AGENTS DANS HAKIMAGENT & ANTIGRAVITY")
    print("=" * 70)

    if not SCRATCH_AGENTS_DIR.exists():
        print(f"[ERREUR] Le dépôt scratch/agency-agents est introuvable à {SCRATCH_AGENTS_DIR}")
        sys.exit(1)

    if not DIVISIONS_FILE.exists():
        print(f"[ERREUR] divisions.json introuvable à {DIVISIONS_FILE}")
        sys.exit(1)

    with open(DIVISIONS_FILE, encoding="utf-8") as f:
        divisions_data = json.load(f)["divisions"]

    print(f"[*] {len(divisions_data)} divisions détectées dans divisions.json")

    # Création des dossiers cibles
    GLOBAL_GEMINI_SKILLS.mkdir(parents=True, exist_ok=True)
    WORKSPACE_AGENTS_SKILLS.mkdir(parents=True, exist_ok=True)
    HAKIM_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    parsed_agents = []

    for div_id, div_info in divisions_data.items():
        div_dir = SCRATCH_AGENTS_DIR / div_id
        if not div_dir.is_dir():
            continue

        for file_path in sorted(div_dir.glob("*.md")):
            content = file_path.read_text(encoding="utf-8")
            if not content.startswith("---"):
                continue

            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            try:
                fm = yaml.safe_load(parts[1])
                if not isinstance(fm, dict):
                    continue
                name = fm.get("name")
                if not name:
                    continue

                description = fm.get("description", "").strip()
                emoji = fm.get("emoji", "🤖")
                color = fm.get("color", div_info.get("color", "#3B82F6"))
                vibe = fm.get("vibe", "").strip()
                slug = slugify(name)
                skill_slug = f"agency-{slug}"
                body = parts[2].strip()

                parsed_agents.append({
                    "name": name,
                    "slug": slug,
                    "skill_slug": skill_slug,
                    "description": description,
                    "emoji": emoji,
                    "color": color,
                    "vibe": vibe,
                    "division": div_id,
                    "division_label": div_info.get("label", div_id.title()),
                    "body": body,
                    "source_file": file_path.name
                })
            except Exception as e:
                print(f"[AVERTISSEMENT] Erreur parsing {file_path}: {e}")

    print(f"[+] {len(parsed_agents)} agents analysés et prêts à être installés.")

    # 1. Écriture des skills Antigravity globaux (~/.gemini/config/skills)
    # 2. Écriture des skills workspace (.agents/skills)
    # 3. Écriture des skills HakimAgent (skills/agency-agents/<division>/<slug>/SKILL.md)
    print("\n[1/4] Installation des fichiers SKILL.md...")
    count_global = 0
    count_workspace = 0
    count_hakim = 0

    for agent in parsed_agents:
        skill_content = (
            f"---\n"
            f"name: {yaml_quote(agent['skill_slug'])}\n"
            f"description: {yaml_quote(agent['description'])}\n"
            f"---\n\n"
            f"{agent['body']}\n"
        )

        # 1. Global Antigravity
        global_skill_dir = GLOBAL_GEMINI_SKILLS / agent["skill_slug"]
        global_skill_dir.mkdir(parents=True, exist_ok=True)
        (global_skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")
        count_global += 1

        # 2. Workspace Antigravity
        ws_skill_dir = WORKSPACE_AGENTS_SKILLS / agent["skill_slug"]
        ws_skill_dir.mkdir(parents=True, exist_ok=True)
        (ws_skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")
        count_workspace += 1

        # 3. HakimAgent Skills Directory (skills/agency-agents/<division>/agency-<slug>/SKILL.md)
        hakim_agent_skill_dir = HAKIM_SKILLS_DIR / agent["division"] / agent["skill_slug"]
        hakim_agent_skill_dir.mkdir(parents=True, exist_ok=True)
        (hakim_agent_skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")
        count_hakim += 1

    print(f"  -> {count_global} skills installés dans {GLOBAL_GEMINI_SKILLS}")
    print(f"  -> {count_workspace} skills installés dans {WORKSPACE_AGENTS_SKILLS}")
    print(f"  -> {count_hakim} skills installés dans {HAKIM_SKILLS_DIR}")

    # 4. Mise à jour de skills/manifest.json
    print("\n[2/4] Mise à jour du catalogue HakimAgent (skills/manifest.json)...")
    manifest = {"generated": "2026-10-11", "total_skills": 0, "skills": []}
    if HAKIM_SKILLS_MANIFEST.exists():
        try:
            with open(HAKIM_SKILLS_MANIFEST, encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as e:
            print(f"[AVERTISSEMENT] Erreur lecture manifest existant: {e}")

    # Retirer les anciens skills agency-agents éventuels pour éviter doublons
    existing_skills = [
        s for s in manifest.get("skills", [])
        if s.get("repo") != "agency-agents" and not s.get("skill", "").startswith("agency-")
    ]

    for agent in parsed_agents:
        rel_path = f"skills/agency-agents/{agent['division']}/{agent['skill_slug']}"
        existing_skills.append({
            "repo": "agency-agents",
            "source_url": "https://github.com/msitarzewski/agency-agents",
            "skill": agent["skill_slug"],
            "path": rel_path,
            "division": agent["division"],
            "division_label": agent["division_label"],
            "emoji": agent["emoji"],
            "description": agent["description"]
        })

    manifest["skills"] = existing_skills
    manifest["total_skills"] = len(existing_skills)
    manifest["generated"] = "2026-10-11"

    with open(HAKIM_SKILLS_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"  -> skills/manifest.json mis à jour : {manifest['total_skills']} compétences au total.")

    # 5. Mise à jour de agent_roles/manifest.json
    print("\n[3/4] Mise à jour des rôles d'agents (agent_roles/manifest.json)...")
    roles_manifest = {"generated": "2026-10-11", "total_roles": 0, "roles": []}
    if HAKIM_ROLES_MANIFEST.exists():
        try:
            with open(HAKIM_ROLES_MANIFEST, encoding="utf-8") as f:
                roles_manifest = json.load(f)
        except Exception as e:
            print(f"[AVERTISSEMENT] Erreur lecture roles manifest existant: {e}")

    # Garder les rôles natifs (qui ne commencent pas par AGENCY_)
    base_roles = [
        r for r in roles_manifest.get("roles", [])
        if not r.get("id", "").startswith("AGENCY_")
    ]

    for agent in parsed_agents:
        role_id = f"AGENCY_{agent['slug'].replace('-', '_').upper()}"
        instructions = (
            f"\nSPÉCIALITÉ: {agent['description']}\n"
            f"VIBE / APPROCHE: {agent['vibe'] if agent['vibe'] else 'Excellence opérationnelle et livrables clairs'}\n"
            f"DIVISION: {agent['division_label']}\n"
        )
        base_roles.append({
            "id": role_id,
            "name": f"{agent['name']} ({agent['division_label']})",
            "icon": agent["emoji"],
            "division": agent["division"],
            "skill": agent["skill_slug"],
            "instructions": instructions
        })

    roles_manifest["roles"] = base_roles
    roles_manifest["total_roles"] = len(base_roles)
    roles_manifest["generated"] = "2026-10-11"

    with open(HAKIM_ROLES_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(roles_manifest, f, indent=2, ensure_ascii=False)

    print(f"  -> agent_roles/manifest.json mis à jour : {roles_manifest['total_roles']} rôles au total.")

    # 6. Sauvegarde d'un fichier de métadonnées complet agency_agents_catalog.json
    catalog_path = PROJECT_ROOT / "backend" / "axiom" / "data" / "agency_agents_catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_agents": len(parsed_agents),
            "divisions": divisions_data,
            "agents": parsed_agents
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[4/4] Catalogue structuré sauvegardé dans {catalog_path}")
    print("\n" + "=" * 70)
    print(f"  SUCCÈS : {len(parsed_agents)} AGENTS AGENCY INSTALLÉS AVEC SUCCÈS !")
    print("=" * 70)

if __name__ == "__main__":
    main()
