from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]
    score: float


def validate(result: Any, criteria: dict = None) -> dict:
    """Validate a result against criteria"""
    criteria = criteria or {}
    errors = []
    warnings = []

    # Check if result is None
    if result is None:
        errors.append("Result is None")
        return {"valid": False, "errors": errors, "warnings": warnings, "score": 0.0}

    # Check required fields
    if isinstance(result, dict):
        required_fields = criteria.get("required_fields", [])
        for field in required_fields:
            if field not in result:
                errors.append(f"Missing required field: {field}")

        # Check for empty fields
        for key, value in result.items():
            if value is None or value == "":
                warnings.append(f"Empty value for key: {key}")

    # Check type
    expected_type = criteria.get("type")
    if expected_type:
        if expected_type == "list" and not isinstance(result, list):
            errors.append(f"Expected list, got {type(result).__name__}")
        elif expected_type == "dict" and not isinstance(result, dict):
            errors.append(f"Expected dict, got {type(result).__name__}")
        elif expected_type == "string" and not isinstance(result, str):
            errors.append(f"Expected string, got {type(result).__name__}")

    # Calculate score
    score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)
    score = max(0.0, min(1.0, score))

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "score": score,
    }
