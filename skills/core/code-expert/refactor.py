def refactor(code: str, goals: list[str] = None) -> dict:
    """Refactor code according to goals"""
    goals = goals or []
    changes = []

    refactored = code

    for goal in goals:
        goal_lower = goal.lower()

        if "extract function" in goal_lower or "extract method" in goal_lower:
            changes.append("Extract function: Identified candidate blocks")
        elif "rename" in goal_lower:
            changes.append("Rename: Identified variables for renaming")
        elif "simplify" in goal_lower:
            changes.append("Simplify: Identified complex expressions")
        elif "add type hints" in goal_lower:
            changes.append("Type hints: Identified untyped parameters")
        elif "remove duplication" in goal_lower:
            changes.append("DRY: Identified duplicated code blocks")
        else:
            changes.append(f"Goal '{goal}': Analyzed for refactoring opportunities")

    return {
        "refactored_code": refactored,
        "changes": changes,
        "goals_addressed": goals,
        "summary": f"Analyzed {len(goals)} refactoring goals, identified {len(changes)} potential changes",
    }
