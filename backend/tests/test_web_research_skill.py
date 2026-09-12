import pytest
from pathlib import Path
import sys
import importlib.util

def _import_from(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

_base = Path(__file__).parent.parent.parent / "skills" / "core" / "web-research"
_wr_search = _import_from("wr_search", _base / "search.py")
_wr_extract = _import_from("wr_extract", _base / "extract.py")
_wr_fact_check = _import_from("wr_fact_check", _base / "fact_check.py")

search = _wr_search.search
extract = _wr_extract.extract
fact_check = _wr_fact_check.fact_check


def test_search():
    """Test web search"""
    result = search("Python programming")

    assert "results" in result
    assert "count" in result


def test_extract():
    """Test URL content extraction"""
    result = extract("https://example.com")

    assert "title" in result
    assert "content" in result
    assert result["url"] == "https://example.com"


def test_fact_check():
    """Test fact checking"""
    result = fact_check("Python is a programming language")

    assert "statement" in result
    assert "confidence" in result
    assert "verdict" in result
