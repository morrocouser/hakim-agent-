import os
from pathlib import Path

BLOCKED_DIRECTORIES_WIN = ("windows", "system32", "program files", "program files (x86)")
BLOCKED_DIRECTORIES_UNIX = ("/etc/shadow", "/etc/sudoers", "/proc", "/sys")
PROTECTED_READ_PATTERNS = {
    "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa", "known_hosts",
    ".env", ".env.local", ".env.production",
}


def _is_safe_read_target(file_path: Path) -> tuple[bool, str]:
    try:
        resolved = file_path.resolve()
        resolved_str = str(resolved).lower()

        if os.name == "nt":
            for win_dir in BLOCKED_DIRECTORIES_WIN:
                if f":\\{win_dir}" in resolved_str:
                    return False, f"Lecture interdite dans les répertoires système Windows ({win_dir})"
        else:
            for unix_dir in BLOCKED_DIRECTORIES_UNIX:
                if resolved_str.startswith(unix_dir):
                    return False, f"Lecture interdite dans les répertoires système ({unix_dir})"

        name_lower = resolved.name.lower()
        if name_lower in PROTECTED_READ_PATTERNS or name_lower.startswith(".env"):
            return False, "Lecture des secrets et clés privées interdite (.env, SSH)"

        return True, ""
    except Exception as e:
        return False, f"Validation de chemin échouée : {e}"


def read(path: str, encoding: str = "utf-8") -> dict:
    """Read file contents with safety validation"""
    try:
        file_path = Path(path)
        if not file_path.exists():
            return {"error": f"File not found: {path}"}

        if not file_path.is_file():
            return {"error": f"Not a file: {path}"}

        is_safe, error_msg = _is_safe_read_target(file_path)
        if not is_safe:
            return {"error": f"[SÉCURITÉ] {error_msg}"}

        content = file_path.read_text(encoding=encoding)
        return {"content": content, "size": len(content)}
    except Exception as e:
        return {"error": str(e)}
