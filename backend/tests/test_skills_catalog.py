"""Test du catalogue de skills intégrés (dépôts GitHub). Exécuté: backend\.venv\Scripts\python.exe -X utf8 backend\tests\test_skills_catalog.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # backend/

from axiom.skills_catalog import list_skills, get_skill, search_skills, get_skill_readme


def test_list_skills():
    skills = list_skills()
    assert len(skills) >= 100, f"expected >=100 skills, got {len(skills)}"
    names = {s["skill"] for s in skills}
    assert {"karpathy-guidelines", "taste-skill"} <= names, names


def test_get_skill():
    s = get_skill("taste-skill", "taste-skill")
    assert s is not None
    assert s["repo"] == "taste-skill"
    readme = get_skill_readme("taste-skill", "taste-skill")
    assert readme and "SKILL" in readme.upper()


def test_search_skills():
    results = search_skills("karpathy")
    assert results and results[0]["skill"] == "karpathy-guidelines"
    assert get_skill("nope", "x") is None


def main():
    test_list_skills()
    test_get_skill()
    test_search_skills()
    print("ALL PASS")


if __name__ == "__main__":
    main()
