import pytest
from pathlib import Path
from axiom.skills.registry import SkillRegistry


def test_registry_initialization(tmp_path):
    """Test registry initializes and scans skills directory"""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    registry = SkillRegistry(skills_dir)

    assert registry.all_skills() == []


def test_registry_indexes_skills(tmp_path):
    """Test registry indexes skills from SKILL.md files"""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir()

    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: test-skill
description: "Test skill"
version: "1.0.0"
tools: ["tool_a"]
triggers: ["test"]
---
""")

    registry = SkillRegistry(skills_dir)
    skills = registry.all_skills()

    assert len(skills) == 1
    assert skills[0].name == "test-skill"


def test_registry_find_by_tool(tmp_path):
    """Test finding skills by tool name"""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir()

    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: test-skill
description: "Test skill"
version: "1.0.0"
tools: ["my_tool"]
triggers: ["test"]
---
""")

    registry = SkillRegistry(skills_dir)
    found = registry.find_by_tool("my_tool")

    assert len(found) == 1
    assert found[0].name == "test-skill"


def test_registry_find_by_trigger(tmp_path):
    """Test finding skills by trigger keyword"""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir()

    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: test-skill
description: "Test skill"
version: "1.0.0"
tools: ["tool_a"]
triggers: ["plan", "decompose"]
---
""")

    registry = SkillRegistry(skills_dir)
    found = registry.find_by_trigger("plan")

    assert len(found) == 1
    assert found[0].name == "test-skill"


def test_registry_get_skill(tmp_path):
    """Test getting skill by name"""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir()

    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: test-skill
description: "Test skill"
version: "1.0.0"
tools: ["tool_a"]
---
""")

    registry = SkillRegistry(skills_dir)
    skill = registry.get_skill("test-skill")

    assert skill is not None
    assert skill.name == "test-skill"
    assert registry.get_skill("nonexistent") is None


def test_registry_refresh(tmp_path):
    """Test refreshing registry after filesystem changes"""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    registry = SkillRegistry(skills_dir)
    assert len(registry.all_skills()) == 0

    skill_dir = skills_dir / "new-skill"
    skill_dir.mkdir()

    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: new-skill
description: "New skill"
version: "1.0.0"
tools: ["tool_a"]
---
""")

    registry.refresh()
    assert len(registry.all_skills()) == 1
