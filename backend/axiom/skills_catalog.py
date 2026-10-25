"""Catalog of integrated agent skills (from GitHub skill repositories).

Skills are stored under the project ``skills/`` directory, each skill is a
folder containing a SKILL.md (agent-skills format). ``manifest.json`` lists
every integrated skill with its source repository.
"""

from __future__ import annotations

import json
import re
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


# Per-field weight of a query term match: a hit in the skill name counts
# more than a hit in its repository, which counts more than the description.
_FIELD_WEIGHTS = (("skill", 5), ("repo", 2), ("description", 1))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def score_skill(skill: dict, terms: list[str], phrase: str = "") -> tuple[int, int]:
    """Return (matched_terms, weighted_score) for a skill against query terms.

    Skills matching more distinct terms always rank first; the weighted score
    breaks ties. An exact skill-name match and a full-phrase match get a bonus.
    """
    fields = {k: str(skill.get(k, "")).lower() for k, _ in _FIELD_WEIGHTS}
    matched = 0
    score = 0
    for term in terms:
        term_score = sum(w for k, w in _FIELD_WEIGHTS if term in fields[k])
        if term_score:
            matched += 1
            score += term_score
    if phrase:
        if fields["skill"] == phrase.replace(" ", "-"):
            score += 10
        elif phrase in fields["description"] or phrase in fields["skill"]:
            score += 3
    return matched, score


def search_skills(query: str, limit: int = 20) -> list[dict]:
    """Search skills by name/description/repo, ranked by relevance.

    The query is split into terms (case-insensitive); a skill matches if it
    contains at least one term, and skills matching every term come first.
    """
    terms = list(dict.fromkeys(_tokenize(query)))
    if not terms:
        return []
    phrase = " ".join(terms)
    scored = []
    for index, s in enumerate(list_skills()):
        matched, score = score_skill(s, terms, phrase)
        if matched:
            # The original index keeps the order stable for equal scores.
            scored.append((-matched, -score, index, s))
    scored.sort(key=lambda item: item[:3])
    return [s for *_, s in scored[:limit]]
