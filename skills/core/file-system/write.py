import os
import re
from pathlib import Path

# Extensions dangereuses dont l'écriture directe est bloquée
BLOCKED_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bat", ".cmd", ".ps1", ".vbs", ".msi", ".com"
}

# Fichiers sensibles protégés contre l'écrasement
PROTECTED_FILENAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519", "known_hosts"
}

# Répertoires système interdits
BLOCKED_DIRECTORIES_WIN = ("windows", "system32", "program files", "program files (x86)")
BLOCKED_DIRECTORIES_UNIX = ("/etc", "/boot", "/bin", "/sbin", "/usr/bin", "/usr/sbin", "/proc", "/sys")


def _is_safe_target(file_path: Path) -> tuple[bool, str]:
    try:
        resolved = file_path.resolve()
        resolved_str = str(resolved).lower()

        # 1. Vérifier si chemin système bloqué
        if os.name == "nt":
            for win_dir in BLOCKED_DIRECTORIES_WIN:
                if f":\\{win_dir}" in resolved_str:
                    return False, f"Accès interdit aux répertoires système Windows ({win_dir})"
        else:
            for unix_dir in BLOCKED_DIRECTORIES_UNIX:
                if resolved_str.startswith(unix_dir):
                    return False, f"Accès interdit aux répertoires système ({unix_dir})"

        # 2. Vérifier les fichiers sensibles
        if resolved.name.lower() in PROTECTED_FILENAMES or resolved.name.startswith(".env"):
            return False, f"Modification du fichier protégé interdite : {resolved.name}"

        # 3. Vérifier les extensions dangereuses
        if resolved.suffix.lower() in BLOCKED_EXTENSIONS:
            return False, f"Écriture d'exécutables interdite : {resolved.suffix}"

        return True, ""
    except Exception as e:
        return False, f"Validation de chemin échouée : {e}"


def write(path: str, content: str, encoding: str = "utf-8") -> dict:
    """Write content to file with safety validation"""
    try:
        file_path = Path(path)
        is_safe, error_msg = _is_safe_target(file_path)
        if not is_safe:
            return {"error": f"[SÉCURITÉ] {error_msg}", "success": False}

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding=encoding)
        return {"success": True, "size": len(content)}
    except Exception as e:
        return {"error": str(e), "success": False}
