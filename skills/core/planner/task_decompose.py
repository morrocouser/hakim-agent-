from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    name: str
    description: str
    dependencies: list[str] = None
    priority: int = 1
    estimated_time: str = "unknown"


def task_decompose(objective: str) -> list[dict]:
    """Break down high-level objectives into ordered, dependency-aware tasks"""
    tasks = []

    # Common decomposition patterns
    patterns = {
        "api": [
            {"name": "design_schema", "description": "Design data schema", "dependencies": []},
            {"name": "implement_auth", "description": "Implement authentication", "dependencies": ["design_schema"]},
            {"name": "create_endpoints", "description": "Create API endpoints", "dependencies": ["design_schema", "implement_auth"]},
            {"name": "write_tests", "description": "Write tests", "dependencies": ["create_endpoints"]},
        ],
        "web": [
            {"name": "design_ui", "description": "Design UI components", "dependencies": []},
            {"name": "implement_frontend", "description": "Implement frontend", "dependencies": ["design_ui"]},
            {"name": "connect_backend", "description": "Connect to backend", "dependencies": ["implement_frontend"]},
            {"name": "test_integration", "description": "Test integration", "dependencies": ["connect_backend"]},
        ],
        "default": [
            {"name": "analyze_requirements", "description": "Analyze requirements", "dependencies": []},
            {"name": "design_solution", "description": "Design solution", "dependencies": ["analyze_requirements"]},
            {"name": "implement", "description": "Implement solution", "dependencies": ["design_solution"]},
            {"name": "test", "description": "Test implementation", "dependencies": ["implement"]},
            {"name": "validate", "description": "Validate results", "dependencies": ["test"]},
        ],
    }

    # Detect pattern from objective
    objective_lower = objective.lower()
    if "api" in objective_lower or "endpoint" in objective_lower:
        pattern = patterns["api"]
    elif "web" in objective_lower or "ui" in objective_lower or "frontend" in objective_lower:
        pattern = patterns["web"]
    else:
        pattern = patterns["default"]

    # Customize descriptions based on objective
    for task in pattern:
        customized = task.copy()
        if "design" in task["name"]:
            customized["description"] = f"{task['description']} for: {objective}"
        elif "implement" in task["name"]:
            customized["description"] = f"{task['description']} for: {objective}"
        tasks.append(customized)

    return tasks
