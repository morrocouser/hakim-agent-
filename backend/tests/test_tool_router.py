import pytest
from pathlib import Path
from axiom.skills.registry import SkillRegistry
from axiom.skills.router import ToolRouter, RouteResult


@pytest.fixture
def registry_with_skills(tmp_path):
    """Create a registry with test skills"""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    planner_dir = skills_dir / "planner"
    planner_dir.mkdir()

    planner_md = planner_dir / "SKILL.md"
    planner_md.write_text("""---
name: planner
description: "Decomposes objectives into executable steps"
version: "1.0.0"
tools: ["task_decompose", "dependency_graph"]
triggers:
  - "plan"
  - "decompose"
  - "roadmap"
---
""")

    return SkillRegistry(skills_dir)


def test_router_initialization(registry_with_skills):
    """Test router initializes with registry"""
    router = ToolRouter(registry_with_skills)
    assert router.registry == registry_with_skills


async def test_router_exact_trigger_match(registry_with_skills):
    """Test routing by exact trigger match"""
    router = ToolRouter(registry_with_skills)
    result = await router.route("plan", {})

    assert isinstance(result, RouteResult)
    assert result.skill_name == "planner"
    assert result.confidence >= 0.9


async def test_router_keyword_match(registry_with_skills):
    """Test routing by keyword overlap"""
    router = ToolRouter(registry_with_skills)
    result = await router.route("decompose this task", {})

    assert isinstance(result, RouteResult)
    assert result.skill_name == "planner"


async def test_router_no_match_raises(registry_with_skills):
    """Test that routing raises ValueError when no match found"""
    router = ToolRouter(registry_with_skills)

    with pytest.raises(ValueError, match="No skill found"):
        await router.route("completely unrelated intent", {})
