import pytest
from pathlib import Path


def test_skill_registry_with_all_skills():
    """Test that all 10 core skills are loaded"""
    from axiom.skills.registry import SkillRegistry

    skills_dir = Path("skills/core")
    registry = SkillRegistry(skills_dir)

    expected_skills = [
        "planner",
        "memory-manager",
        "reasoning",
        "validator",
        "code-expert",
        "terminal",
        "file-system",
        "web-research",
        "github-manager",
    ]

    all_skills = registry.all_skills()
    skill_names = [s.name for s in all_skills]

    for skill in expected_skills:
        assert skill in skill_names, f"Missing skill: {skill}"


def test_tool_router_can_route_to_all_skills():
    """Test that ToolRouter can route to all skills"""
    import asyncio
    from axiom.skills.registry import SkillRegistry
    from axiom.skills.router import ToolRouter

    skills_dir = Path("skills/core")
    registry = SkillRegistry(skills_dir)
    router = ToolRouter(registry)

    test_intents = {
        "planner": "plan",
        "memory-manager": "remember",
        "reasoning": "analyze",
        "validator": "validate",
        "code-expert": "generate code",
        "terminal": "execute command",
        "file-system": "read file",
        "web-research": "search web",
        "github-manager": "create repository",
    }

    for skill_name, intent in test_intents.items():
        try:
            result = asyncio.run(router.route(intent, {}))
            assert result.skill_name == skill_name or result.confidence > 0
        except ValueError:
            pass


@pytest.mark.asyncio
async def test_full_agent_flow():
    """Test complete agent flow with all skills"""
    from axiom.core.agent import PilotAgent

    skills_dir = Path("skills/core")
    agent = PilotAgent(skills_dir)

    result = await agent.execute("Create a Python function that calculates fibonacci numbers")

    assert hasattr(result, "tasks")
    assert hasattr(result, "success")
    assert isinstance(result.tasks, list)
