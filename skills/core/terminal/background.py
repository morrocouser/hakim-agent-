import subprocess
import os
import sys
from pathlib import Path

# Add current skill dir to import validate_terminal_command
sys.path.insert(0, str(Path(__file__).parent))
from execute import validate_terminal_command


def background(command: str, cwd: str = None) -> dict:
    """Run a command in background with safety checks"""
    is_valid, error_msg = validate_terminal_command(command, cwd)
    if not is_valid:
        return {
            "pid": None,
            "status": "failed",
            "error": f"[SÉCURITÉ] {error_msg}",
        }

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=cwd,
        )

        return {
            "pid": process.pid,
            "status": "started",
            "command": command,
        }
    except Exception as e:
        return {
            "pid": None,
            "status": "failed",
            "error": str(e),
        }
