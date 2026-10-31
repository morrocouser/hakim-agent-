import os
import re
import subprocess
from pathlib import Path

# Commandes destructives ou à haut risque
BLOCKED_COMMAND_PATTERNS = [
    r"\brm\s+-[rRfF]*\s+[/~]",
    r"\brmdir\s+/[sS]\s+/[qQ]\s+[a-zA-Z]:\\",
    r"\bdel\s+/[fF]\s+/[sS]\s+/[qQ]\s+[a-zA-Z]:\\",
    r"\bformat\s+[a-zA-Z]:",
    r"\bmkfs\b",
    r":\(\)\s*\{\s*:\|:&\s*\};:",  # Fork bomb
    r"\bshutdown\b",
    r"\breboot\b",
    r"\binit\s+0\b",
    r"\bnc\s+.*-e\b",
    r"\bbash\s+-i\s+>&",
    r"\bpowershell.*-enc(odedcommand)?\b",
    r"\breg\s+(delete|add)\s+hklm",
]

# Répertoires système interdits en tant que cwd
BLOCKED_CWD_WIN = ("windows", "system32", "program files")
BLOCKED_CWD_UNIX = ("/etc", "/boot", "/bin", "/sbin", "/usr/bin", "/sys", "/proc")


def validate_terminal_command(command: str, cwd: str = None) -> tuple[bool, str]:
    if not command or not command.strip():
        return False, "Commande vide"

    # Vérification des motifs dangereux
    for pattern in BLOCKED_COMMAND_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Commande dangereuse bloquée par la politique de sécurité : {pattern}"

    # Vérification du répertoire de travail (cwd)
    if cwd:
        try:
            resolved_cwd = Path(cwd).resolve()
            cwd_str = str(resolved_cwd).lower()
            if os.name == "nt":
                for b_win in BLOCKED_CWD_WIN:
                    if f":\\{b_win}" in cwd_str:
                        return False, f"Exécution interdite dans le répertoire système ({b_win})"
            else:
                for b_unix in BLOCKED_CWD_UNIX:
                    if cwd_str.startswith(b_unix):
                        return False, f"Exécution interdite dans le répertoire système ({b_unix})"
        except Exception as e:
            return False, f"CWD invalide : {e}"

    return True, ""


def execute(command: str, timeout: int = 60, cwd: str = None) -> dict:
    """Execute a shell command with safety checks"""
    is_valid, error_msg = validate_terminal_command(command, cwd)
    if not is_valid:
        return {
            "stdout": "",
            "stderr": f"[SÉCURITÉ] {error_msg}",
            "returncode": -1,
            "success": False,
        }

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "returncode": -1,
            "success": False,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "success": False,
        }
