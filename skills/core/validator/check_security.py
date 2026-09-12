import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SecurityResult:
    safe: bool
    vulnerabilities: list[dict]
    recommendations: list[str]


def check_security(code: str) -> dict:
    """Check code for security vulnerabilities"""
    vulnerabilities = []
    recommendations = []

    patterns = [
        {"pattern": r"eval\s*\(", "name": "eval() usage", "severity": "high",
         "recommendation": "Avoid eval() - use ast.literal_eval() or specific parsing"},
        {"pattern": r"exec\s*\(", "name": "exec() usage", "severity": "high",
         "recommendation": "Avoid exec() - use importlib or specific execution"},
        {"pattern": r"os\.system\s*\(", "name": "os.system() usage", "severity": "medium",
         "recommendation": "Use subprocess.run() with shell=False"},
        {"pattern": r"subprocess\.call.*shell=True", "name": "subprocess with shell=True",
         "severity": "medium", "recommendation": "Use shell=False and pass arguments as list"},
        {"pattern": r"password\s*=\s*['\"]", "name": "Hardcoded password", "severity": "high",
         "recommendation": "Use environment variables or secrets manager"},
        {"pattern": r"SELECT.*FROM.*WHERE.*=.*\+", "name": "SQL injection risk",
         "severity": "high", "recommendation": "Use parameterized queries"},
    ]

    for pattern_info in patterns:
        matches = list(re.finditer(pattern_info["pattern"], code, re.IGNORECASE))
        for match in matches:
            line_number = code[:match.start()].count("\n") + 1
            vulnerabilities.append({
                "type": pattern_info["name"],
                "severity": pattern_info["severity"],
                "line": line_number,
                "position": match.start(),
            })
            recommendations.append(pattern_info["recommendation"])

    return {
        "safe": len(vulnerabilities) == 0,
        "vulnerabilities": vulnerabilities,
        "recommendations": list(set(recommendations)),
    }
