import pytest
from pathlib import Path
import sys

# Add skills directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "core" / "reasoning"))

from strategy_select import strategy_select
from analyze import analyze
from recover import recover


def test_strategy_select_debug():
    """Test strategy selection for debug problems"""
    result = strategy_select("The API is returning 500 errors")

    assert result["name"] == "debug"
    assert "reproduce" in result["steps"][0].lower()


def test_strategy_select_optimize():
    """Test strategy selection for optimization problems"""
    result = strategy_select("The application is running slowly")

    assert result["name"] == "optimize"
    assert "profile" in result["steps"][0].lower()


def test_strategy_select_refactor():
    """Test strategy selection for refactoring"""
    result = strategy_select("We need to clean up the codebase")

    assert result["name"] == "refactor"


def test_strategy_select_default():
    """Test strategy selection defaults to implement"""
    result = strategy_select("Build a new feature")

    assert result["name"] == "implement"


def test_analyze_dict():
    """Test analyzing dictionary data"""
    data = {"name": "test", "value": None}
    criteria = {"required_fields": ["name", "value"]}

    result = analyze(data, criteria)

    assert result["passed"] is False
    assert len(result["issues"]) == 1
    assert "value" in result["issues"][0]


def test_analyze_list():
    """Test analyzing list data"""
    data = ["item1", "", "item3"]
    criteria = {"min_length": 2}

    result = analyze(data, criteria)

    assert result["passed"] is False
    assert len(result["issues"]) == 1
    assert "Empty item" in result["issues"][0]


def test_analyze_clean():
    """Test analyzing clean data"""
    data = {"name": "test", "value": "ok"}
    criteria = {"required_fields": ["name", "value"]}

    result = analyze(data, criteria)

    assert result["passed"] is True
    assert result["score"] == 1.0


def test_recover():
    """Test error recovery"""
    failed_results = [
        {"error": "timeout exceeded"},
        {"error": "permission denied"},
        {"error": "not found"},
    ]

    result = recover(failed_results, "test objective")

    assert result["recovered"] is True
    assert len(result["results"]) == 3
    assert len(result["adjustments"]) == 3
