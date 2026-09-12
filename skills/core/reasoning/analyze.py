from dataclasses import dataclass
from typing import Any


@dataclass
class Analysis:
    passed: bool
    issues: list[str]
    recommendations: list[str]
    score: float


def analyze(data: Any, criteria: dict = None) -> dict:
    """Analyze data against criteria to identify issues"""
    criteria = criteria or {}
    issues = []
    recommendations = []

    # Basic analysis based on data type
    if isinstance(data, dict):
        # Check for required fields
        required = criteria.get("required_fields", [])
        for field in required:
            if field not in data:
                issues.append(f"Missing required field: {field}")
                recommendations.append(f"Add {field} to the data")

        # Check for empty values
        for key, value in data.items():
            if value is None or value == "":
                issues.append(f"Empty value for key: {key}")
                recommendations.append(f"Provide value for {key}")

    elif isinstance(data, list):
        # Check list length
        min_length = criteria.get("min_length", 0)
        if len(data) < min_length:
            issues.append(f"List too short: {len(data)} < {min_length}")
            recommendations.append(f"Add more items to reach minimum length {min_length}")

        # Check for empty items
        for i, item in enumerate(data):
            if item is None or item == "":
                issues.append(f"Empty item at index {i}")
                recommendations.append(f"Remove or fill empty item at index {i}")

    elif isinstance(data, str):
        # Check string length
        min_length = criteria.get("min_length", 0)
        if len(data) < min_length:
            issues.append(f"String too short: {len(data)} < {min_length}")
            recommendations.append(f"Extend string to meet minimum length {min_length}")

    # Calculate score
    score = 1.0 - (len(issues) * 0.1)
    score = max(0.0, min(1.0, score))

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "recommendations": recommendations,
        "score": score,
    }
