import pytest
from pathlib import Path
import sys
import os

# Add skills directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "core" / "terminal"))

from execute import execute
from background import background


def test_execute_simple_command():
    """Test executing a simple command"""
    if os.name == "nt":
        result = execute("echo Hello, World!")
    else:
        result = execute("echo 'Hello, World!'")

    assert result["success"] is True
    assert "Hello, World!" in result["stdout"]


def test_execute_with_timeout():
    """Test executing command with timeout"""
    if os.name == "nt":
        result = execute("timeout /t 10", timeout=1)
    else:
        result = execute("sleep 10", timeout=1)

    assert result["success"] is False


def test_background_process():
    """Test running command in background"""
    if os.name == "nt":
        result = background("timeout /t 5")
    else:
        result = background("sleep 5")

    assert result["status"] == "started"
    assert result["pid"] is not None
