from dataclasses import dataclass
from typing import Optional


@dataclass
class Strategy:
    name: str
    description: str
    steps: list[str]
    confidence: float


def strategy_select(problem: str, context: dict = None) -> dict:
    """Select the best strategy for a given problem"""
    context = context or {}
    problem_lower = problem.lower()

    # Strategy selection based on problem type
    strategies = {
        "debug": Strategy(
            name="debug",
            description="Systematic debugging approach",
            steps=[
                "reproduce the issue",
                "isolate the problem",
                "identify root cause",
                "implement fix",
                "verify fix",
            ],
            confidence=0.9,
        ),
        "optimize": Strategy(
            name="optimize",
            description="Performance optimization",
            steps=[
                "profile current performance",
                "identify bottlenecks",
                "implement optimizations",
                "measure improvement",
            ],
            confidence=0.85,
        ),
        "refactor": Strategy(
            name="refactor",
            description="Code refactoring",
            steps=[
                "analyze current structure",
                "identify improvement areas",
                "refactor incrementally",
                "run tests",
                "verify behavior",
            ],
            confidence=0.8,
        ),
        "implement": Strategy(
            name="implement",
            description="Feature implementation",
            steps=[
                "understand requirements",
                "design solution",
                "implement core logic",
                "add tests",
                "document",
            ],
            confidence=0.85,
        ),
    }

    # Select strategy based on keywords
    if "error" in problem_lower or "bug" in problem_lower or "debug" in problem_lower:
        return strategies["debug"].__dict__
    elif "slow" in problem_lower or "performance" in problem_lower:
        return strategies["optimize"].__dict__
    elif "clean" in problem_lower or "refactor" in problem_lower:
        return strategies["refactor"].__dict__
    else:
        return strategies["implement"].__dict__
