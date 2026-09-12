import ast
from dataclasses import dataclass
from typing import Optional


@dataclass
class SyntaxResult:
    valid: bool
    error: Optional[str]
    line: Optional[int]
    column: Optional[int]


def check_syntax(code: str, language: str = "python") -> dict:
    """Check code syntax for errors"""
    if language.lower() == "python":
        return _check_python_syntax(code)
    else:
        return {"valid": True, "error": None, "line": None, "column": None}


def _check_python_syntax(code: str) -> dict:
    """Check Python syntax"""
    try:
        ast.parse(code)
        return {"valid": True, "error": None, "line": None, "column": None}
    except SyntaxError as e:
        return {
            "valid": False,
            "error": str(e),
            "line": e.lineno,
            "column": e.offset,
        }
