from dataclasses import dataclass
from typing import Optional


@dataclass
class Timeline:
    total_tasks: int
    parallel_groups: int
    estimated_duration: str
    schedule: list[dict]


def schedule(tasks: list[dict], constraints: dict = None) -> dict:
    """Generate execution timeline respecting resource constraints"""
    constraints = constraints or {}
    max_parallel = constraints.get("max_parallel", 3)

    # Build dependency graph
    in_degree = {task["name"]: 0 for task in tasks}
    for task in tasks:
        for dep in task.get("dependencies", []):
            if dep in in_degree:
                in_degree[task["name"]] += 1

    # Create schedule with parallel groups
    schedule_items = []
    executed = set()
    remaining = set(in_degree.keys())

    step = 1
    while remaining:
        # Find tasks that can execute now
        ready = [name for name in remaining if in_degree[name] == 0]

        # Limit parallelism
        ready = ready[:max_parallel]

        if not ready:
            # Deadlock detection
            raise ValueError(f"Circular dependency detected: {remaining}")

        # Add to schedule
        for task_name in ready:
            task = next(t for t in tasks if t["name"] == task_name)
            schedule_items.append({
                "step": step,
                "task": task_name,
                "description": task.get("description", ""),
                "dependencies": task.get("dependencies", []),
                "parallel": len(ready) > 1,
            })
            executed.add(task_name)
            remaining.remove(task_name)

        # Update in-degrees
        for task_name in ready:
            for other in remaining:
                other_task = next(t for t in tasks if t["name"] == other)
                if task_name in other_task.get("dependencies", []):
                    in_degree[other] -= 1

        step += 1

    return {
        "total_tasks": len(tasks),
        "parallel_groups": len(set(item["step"] for item in schedule_items)),
        "estimated_duration": f"{len(schedule_items)} steps",
        "schedule": schedule_items,
    }
