import pytest
from pathlib import Path


def test_pilot_agent_initialization(tmp_path):
    """Test PilotAgent initialization"""
    from axiom.core.agent import PilotAgent

    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    agent = PilotAgent(skills_dir)

    assert agent.registry is not None
    assert agent.router is not None


@pytest.mark.asyncio
async def test_pilot_agent_execute(tmp_path):
    """Test PilotAgent execution with fallback (no planner skill)"""
    from axiom.core.agent import PilotAgent

    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    agent = PilotAgent(skills_dir)
    result = await agent.execute("Build a simple app")

    assert hasattr(result, "tasks")
    assert hasattr(result, "success")
    assert isinstance(result.tasks, list)


@pytest.mark.asyncio
async def test_pilot_agent_with_planner(tmp_path):
    """Test PilotAgent with a planner skill"""
    from axiom.core.agent import PilotAgent

    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    planner_dir = skills_dir / "planner"
    planner_dir.mkdir()

    (planner_dir / "SKILL.md").write_text("""---
name: planner
description: "Decomposes objectives into executable steps"
version: "1.0.0"
tools: ["task_decompose"]
triggers:
  - "plan"
  - "decompose"
---
""")

    (planner_dir / "task_decompose.py").write_text("""def task_decompose(objective: str) -> list:
    return [
        {"name": "task1", "intent": "first step", "params": {}, "dependencies": []},
        {"name": "task2", "intent": "second step", "params": {}, "dependencies": ["task1"]}
    ]
""")

    agent = PilotAgent(skills_dir)
    result = await agent.execute("Build a simple app")

    assert result.success is True
    assert len(result.tasks) == 2
