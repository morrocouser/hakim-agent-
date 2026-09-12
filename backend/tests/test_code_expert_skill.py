import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "core" / "code-expert"))

from generate import generate
from review import review
from refactor import refactor


def test_generate_function():
    """Test generating a function"""
    result = generate("Calculate fibonacci numbers")

    assert "code" in result
    assert result["type"] == "function"
    assert result["language"] == "python"
    assert "def" in result["code"]


def test_generate_class():
    """Test generating a class"""
    result = generate("Create a class for managing users", "python")

    assert "code" in result
    assert result["type"] == "class"
    assert "class" in result["code"]


def test_review_clean():
    """Test reviewing clean code"""
    code = '''def hello():
    """Say hello"""
    return "world"
'''
    result = review(code)

    assert result["passed"] is True
    assert len(result["issues"]) == 0


def test_review_issues():
    """Test reviewing code with issues"""
    code = 'def hello():\n    return "world"'

    result = review(code)

    assert result["passed"] is False
    assert len(result["issues"]) > 0


def test_review_long_line():
    """Test reviewing code with long lines"""
    code = 'x = ' + '"a" ' * 50  # ~150 chars

    result = review(code)

    assert any("too long" in issue.lower() for issue in result["issues"])


def test_refactor():
    """Test refactoring code"""
    code = "def hello(): pass"

    result = refactor(code, ["extract function", "add type hints"])

    assert "changes" in result
    assert len(result["changes"]) == 2
