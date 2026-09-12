"""Catalog of integrated agent skills (from GitHub skill repositories).

Skills are stored under the project ``skills/`` directory, each skill is a
folder containing a SKILL.md (agent-skills format). ``manifest.json`` lists
every integrated skill with its source repository.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

SKILLS_ROOT = Path(__file__).resolve().parent.parent.parent / "skills"
MANIFEST_PATH = SKILLS_ROOT / "manifest.json"


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {"generated": "", "total_skills": 0, "skills": []}
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def list_skills() -> list[dict]:
    """Return all integrated skills from the manifest."""
    return _load_manifest().get("skills", [])


def get_skill(repo: str, skill: str) -> Optional[dict]:
    """Return a single skill definition."""
    for s in list_skills():
        if s.get("repo") == repo and s.get("skill") == skill:
            return s
    return None


def get_skill_readme(repo: str, skill: str) -> Optional[str]:
    """Return the SKILL.md content of a skill, if it exists on disk."""
    skill = get_skill(repo, skill)
    if not skill:
        return None
    skill_path = Path(skill["path"])
    if not skill_path.is_absolute():
        skill_path = SKILLS_ROOT.parent / skill_path
    md = skill_path / "SKILL.md"
    if md.exists():
        return md.read_text(encoding="utf-8", errors="replace")
    return None


def search_skills(query: str, limit: int = 20) -> list[dict]:
    """Search skills by name/description/repo (case-insensitive)."""
    q = query.lower()
    results = []
    for s in list_skills():
        haystack = " ".join(
            str(s.get(k, "")) for k in ("skill", "description", "repo", "source_url")
        ).lower()
        if q in haystack:
            results.append(s)
        if len(results) >= limit:
            break
    return results
