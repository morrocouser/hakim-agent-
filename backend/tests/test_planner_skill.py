import pytest
from pathlib import Path
import sys

# Add skills directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "core" / "planner"))

from task_decompose import task_decompose
from dependency_graph import dependency_graph
from schedule import schedule


def test_task_decompose():
    """Test task decomposition"""
    tasks = task_decompose("Build a REST API with authentication")

    assert len(tasks) >= 3
    assert any("design" in t["name"] for t in tasks)
    assert any("implement" in t["name"] for t in tasks)
    assert any("test" in t["name"] for t in tasks)


def test_task_decompose_web():
    """Test task decomposition for web projects"""
    tasks = task_decompose("Build a web frontend")

    assert len(tasks) >= 3
    assert any("design" in t["name"] for t in tasks)
    assert any("frontend" in t["name"] or "implement" in t["name"] for t in tasks)


def test_dependency_graph():
    """Test dependency graph computation"""
    tasks = [
        {"name": "a", "dependencies": []},
        {"name": "b", "dependencies": ["a"]},
        {"name": "c", "dependencies": ["a"]},
        {"name": "d", "dependencies": ["b", "c"]},
    ]

    graph = dependency_graph(tasks)

    assert "a" in graph["execution_order"]
    assert graph["execution_order"].index("a") < graph["execution_order"].index("b")
    assert graph["execution_order"].index("a") < graph["execution_order"].index("c")


def test_dependency_graph_parallel_groups():
    """Test that parallel groups are computed"""
    tasks = [
        {"name": "a", "dependencies": []},
        {"name": "b", "dependencies": ["a"]},
        {"name": "c", "dependencies": ["a"]},
    ]

    graph = dependency_graph(tasks)

    assert len(graph["parallel_groups"]) >= 2


def test_schedule():
    """Test schedule generation"""
    tasks = [
        {"name": "a", "description": "Task A", "dependencies": []},
        {"name": "b", "description": "Task B", "dependencies": ["a"]},
        {"name": "c", "description": "Task C", "dependencies": ["a"]},
    ]

    result = schedule(tasks)

    assert result["total_tasks"] == 3
    assert len(result["schedule"]) == 3


def test_schedule_circular_dependency():
    """Test that circular dependencies raise ValueError"""
    tasks = [
        {"name": "a", "dependencies": ["b"]},
        {"name": "b", "dependencies": ["a"]},
    ]

    with pytest.raises(ValueError, match="Circular dependency"):
        schedule(tasks)
