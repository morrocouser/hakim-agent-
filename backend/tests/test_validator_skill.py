import pytest
from pathlib import Path
import sys

# Add skills directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "core" / "validator"))

from validate import validate
from check_syntax import check_syntax
from check_security import check_security


def test_validate_dict():
    """Test validating dictionary data"""
    data = {"name": "test", "value": "ok"}
    criteria = {"required_fields": ["name", "value"]}

    result = validate(data, criteria)

    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_dict_missing_field():
    """Test validating dictionary with missing field"""
    data = {"name": "test"}
    criteria = {"required_fields": ["name", "value"]}

    result = validate(data, criteria)

    assert result["valid"] is False
    assert len(result["errors"]) == 1


def test_validate_none():
    """Test validating None"""
    result = validate(None)

    assert result["valid"] is False
    assert result["score"] == 0.0


def test_validate_wrong_type():
    """Test validating with wrong type"""
    data = "hello"
    criteria = {"type": "dict"}

    result = validate(data, criteria)

    assert result["valid"] is False


def test_check_syntax_valid():
    """Test checking valid Python syntax"""
    code = "def hello(): return 'world'"

    result = check_syntax(code, "python")

    assert result["valid"] is True
    assert result["error"] is None


def test_check_syntax_invalid():
    """Test checking invalid Python syntax"""
    code = "def hello( return 'world'"

    result = check_syntax(code, "python")

    assert result["valid"] is False
    assert result["error"] is not None


def test_check_syntax_other_language():
    """Test checking syntax for non-Python language"""
    code = "function hello() { return 'world'; }"

    result = check_syntax(code, "javascript")

    assert result["valid"] is True


def test_check_security_clean():
    """Test checking clean code"""
    code = "def hello(): return 'world'"

    result = check_security(code)

    assert result["safe"] is True
    assert len(result["vulnerabilities"]) == 0


def test_check_security_vulnerable():
    """Test checking vulnerable code"""
    code = "eval(user_input)"

    result = check_security(code)

    assert result["safe"] is False
    assert len(result["vulnerabilities"]) == 1
    assert result["vulnerabilities"][0]["type"] == "eval() usage"


def test_check_security_multiple():
    """Test checking code with multiple vulnerabilities"""
    code = "eval(x)\nexec(y)\npassword = 'secret'"

    result = check_security(code)

    assert result["safe"] is False
    assert len(result["vulnerabilities"]) == 3
