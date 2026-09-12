def review(code: str) -> dict:
    """Review code for issues and improvements"""
    issues = []
    recommendations = []

    lines = code.split("\n")

    # Check for common issues
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Check for long lines
        if len(line) > 120:
            issues.append(f"Line {i}: Line too long ({len(line)} > 120)")
            recommendations.append(f"Break line {i} into multiple lines")

        # Check for missing docstrings
        if stripped.startswith("def ") and "(" in stripped:
            if i < len(lines) and '"""' not in lines[i] and "'''" not in lines[i]:
                issues.append(f"Line {i}: Missing docstring for function")
                recommendations.append(f"Add docstring to function at line {i}")

        # Check for bare except
        if stripped == "except:":
            issues.append(f"Line {i}: Bare except clause")
            recommendations.append(f"Use specific exception types at line {i}")

        # Check for print statements (debug)
        if stripped.startswith("print(") and "debug" not in stripped.lower():
            recommendations.append(f"Line {i}: Consider removing print statement")

    # Calculate score
    score = max(0.0, 1.0 - (len(issues) * 0.1))

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "recommendations": recommendations,
        "score": score,
    }
