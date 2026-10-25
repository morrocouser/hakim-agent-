"""
Secure Code Executor for APEX v4.0

Security features:
- Docker-based sandboxing with resource limits
- Input validation and sanitization
- Blocked dangerous operations
- Automatic cleanup of temp files
- Network isolation
- CPU/Memory constraints
- Security skill integration
"""

from __future__ import annotations

import subprocess
import tempfile
import os
import shutil
import re
from typing import Optional, Tuple
from pathlib import Path
from axiom.logging_setup import log


# === SECURITY CONFIGURATION ===
ALLOWED_LANGUAGES = {"python", "javascript"}  # Bash and SQL disabled for security
MAX_EXECUTION_TIME = 30  # seconds
MAX_MEMORY_MB = 512  # megabytes
MAX_CPU_SHARES = 0.5  # CPU quota (0.5 = 50% of one CPU)
MAX_OUTPUT_BYTES = 100_000  # 100KB output limit
MAX_PIDS = 64  # processus/threads max dans le conteneur
SANDBOX_USER = "65534:65534"  # nobody:nogroup
# Images surchargeables (HAKIM_SANDBOX_IMAGE_PYTHON / _JAVASCRIPT) pour les
# figer par digest : "python:3.11-slim@sha256:..."
DOCKER_IMAGES = {
    "python": os.getenv("HAKIM_SANDBOX_IMAGE_PYTHON", "python:3.11-slim"),
    "javascript": os.getenv("HAKIM_SANDBOX_IMAGE_JAVASCRIPT", "node:18-alpine"),
}

# Try to import security tools for additional validation
try:
    # Le skill est dans backend/skills/security/
    import sys
    from pathlib import Path
    skills_path = Path(__file__).resolve().parent.parent.parent / "skills"
    if str(skills_path) not in sys.path:
        sys.path.insert(0, str(skills_path))
    
    from security.security_tools import validate_code as security_validate_code
    SECURITY_SKILL_AVAILABLE = True
    log.info("Security skill chargé avec succès")
except ImportError as e:
    SECURITY_SKILL_AVAILABLE = False
    log.warning(f"Security skill non disponible: {e} - validation basique uniquement")

# Dangerous patterns to block
DANGEROUS_PATTERNS = {
    "python": [
        r"\bimport\s+os\b",
        r"\bimport\s+subprocess\b",
        r"\bimport\s+sys\b",
        r"\bimport\s+shutil\b",
        r"\bimport\s+socket\b",
        r"\bimport\s+requests\b",
        r"\bimport\s+httpx\b",
        r"\bimport\s+urllib\b",
        r"\bimport\s+ftplib\b",
        r"\bimport\s+pickle\b",
        r"\bimport\s+marshal\b",
        r"\bimport\s+ctypes\b",
        r"\bfrom\s+(os|subprocess|sys|shutil|socket|requests|httpx|urllib|ftplib|pickle|marshal|ctypes)\b",
        r"open\(.*['\"]\./",
        r"\b__import__\(",
        r"\bexec\(",
        r"\beval\(",
        r"\bcompile\(",
        r"\bos\.",
        r"\bsubprocess\.",
        r"\bshutil\.",
        r"\bsys\.exit\(",
        r"\bbreakpoint\(",
        r"\binput\(",
    ],

    "javascript": [
        r"require\('child_process'\)",  # Child process
        r"require\('fs'\)",  # File system
        r"require\('http'\)",  # HTTP
        r"require\('https'\)",  # HTTPS
        r"require\('net'\)",  # Network
        r"require\('dgram'\)",  # UDP
        r"require\('os'\)",  # OS access
        r"eval\(",  # Code evaluation
        r"Function\(",  # Dynamic function
        r"\.exec",  # Execution
        r"\.spawn",  # Process spawning
    ],
}

# Allowed imports for each language (whitelist approach)
ALLOWED_IMPORTS = {
    "python": [
        "math",
        "datetime",
        "json",
        "re",
        "collections",
        "itertools",
        "functools",
        "random",
        "statistics",
        "decimal",
        "fractions",
        "numbers",
        "hashlib",
        "hmac",
        "base64",
        "binascii",
        "struct",
        "array",
        "enum",
        "typing",
        "abc",
        "dataclasses",
        "copy",
        "pprint",
        "string",
        "textwrap",
        "unicodedata",
    ],
    "javascript": [
        "math",
        "date",
        "json",
        "regex",
    ],
}


class SecurityError(Exception):
    """Raised when code fails security validation."""
    pass


class CodeExecutor:
    """
    Secure code executor with sandboxing and input validation.
    
    Uses Docker containers with strict resource limits for isolation.
    All temporary files are automatically cleaned up.
    """

    def __init__(self, docker_enabled: bool = True):
        self.docker_enabled = docker_enabled and shutil.which("docker") is not None
        if not self.docker_enabled:
            log.warning("Docker non disponible - exécution de code DÉSACTIVÉE")

    def validate_code(self, language: str, code: str) -> Tuple[bool, str]:
        """
        Validate code for security threats.
        
        Utilise:
        1. Validation basique (langage, longueur)
        2. Patterns dangereux par langage
        3. Validation des imports (Python)
        4. Skill de sécurité si disponible
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        language = language.lower()
        
        # Check 1: Langage supporté
        if language not in ALLOWED_LANGUAGES:
            return False, f"Langage non supporté: {language}"
        
        # Check 2: Longueur du code
        if len(code) > 50_000:  # 50KB limit
            return False, "Code trop long (max 50KB)"
        
        # Check 3: Patterns dangereux
        patterns = DANGEROUS_PATTERNS.get(language, [])
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Motif dangereux détecté: {pattern[:50]}"
        
        # Check 4: Imports valides (Python)
        if language == "python":
            import_re = r"^(import\s+|from\s+\w+\s+import\s+)([\w.,\s]+)"
            for match in re.finditer(import_re, code, re.MULTILINE):
                import_stmt = match.group(2)
                # Extract module names
                modules = re.split(r"[,\s]", import_stmt)
                for mod in modules:
                    mod = mod.strip()
                    if mod and mod not in ALLOWED_IMPORTS["python"]:
                        # Allow submodules of allowed imports
                        base_mod = mod.split(".")[0]
                        if base_mod not in ALLOWED_IMPORTS["python"]:
                            return False, f"Import non autorisé: {mod}"
        
        # Check 5: Validation avec le skill de sécurité (si disponible)
        if SECURITY_SKILL_AVAILABLE:
            try:
                validation_result = security_validate_code(code, language, strict=True)
                if not validation_result.valid:
                    errors = validation_result.errors or []
                    if errors:
                        return False, f"Validation sécurité échouée: {errors[0]}"
                    return False, "Validation sécurité échouée"
            except Exception as e:
                log.warning(f"Erreur validation skill sécurité: {e}")
                # Ne pas bloquer l'exécution si le skill échoue
                pass
        
        return True, ""

    def _get_docker_command(self, language: str, tmp_dir: str, code: str) -> list:
        """Build Docker command with security constraints."""
        language = language.lower()

        if language == "python":
            image, runner = DOCKER_IMAGES["python"], ["python", "script.py"]
        elif language == "javascript":
            image, runner = DOCKER_IMAGES["javascript"], ["node", "script.mjs"]
        else:
            raise SecurityError(f"Unsupported language: {language}")

        return [
            "docker", "run", "--rm",
            "--memory", f"{MAX_MEMORY_MB}m",
            "--memory-swap", f"{MAX_MEMORY_MB}m",  # pas de swap
            "--cpus", str(MAX_CPU_SHARES),
            "--pids-limit", str(MAX_PIDS),  # anti fork-bomb
            "--network", "none",  # No network access
            "--read-only",  # rootfs en lecture seule
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--user", SANDBOX_USER,  # non-root
            "-v", f"{tmp_dir}:/code:ro",  # code monté en lecture seule
            "-w", "/code",
            image,
            *runner,
        ]

    def _write_code_file(self, tmp_dir: str, language: str, code: str) -> str:
        """Write code to temporary file with validation."""
        language = language.lower()
        
        if language == "python":
            path = os.path.join(tmp_dir, "script.py")
            # Add security header
            secure_code = """# APEX Secure Execution
# Network disabled, limited resources
# All imports validated
""" + code
        elif language == "javascript":
            path = os.path.join(tmp_dir, "script.mjs")
            secure_code = "// APEX Secure Execution\n// Network disabled, limited resources\n" + code
        else:
            raise SecurityError(f"Unsupported language: {language}")
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(secure_code)
        # mkdtemp crée un dossier 0700 : l'utilisateur non-root du conteneur
        # doit pouvoir lire le dossier et le script (monté en :ro).
        os.chmod(tmp_dir, 0o755)
        os.chmod(path, 0o644)

        return path

    def execute(self, language: str, code: str) -> str:
        """
        Execute code in a secure sandbox.
        
        Args:
            language: Programming language ('python' or 'javascript')
            code: Source code to execute
            
        Returns:
            Execution output or error message
        """
        language = language.lower()
        
        # Step 1: Validate input
        is_valid, error_msg = self.validate_code(language, code)
        if not is_valid:
            log.warning(f"Code bloqué pour raison de sécurité: {error_msg}")
            return f"[SÉCURITÉ] Code bloqué: {error_msg}"
        
        # Step 2: Check Docker availability
        if not self.docker_enabled:
            return "[Erreur] Docker requis pour l'exécution sécurisée. Installez Docker."
        
        # Step 3: Verify Docker is running
        try:
            subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5
            )
        except Exception:
            return "[Erreur] Docker n'est pas en cours d'exécution. Démarrez Docker."
        
        # Step 4: Execute in sandbox
        try:
            tmp_dir = tempfile.mkdtemp(prefix="apex_code_")
            
            try:
                # Write code file
                self._write_code_file(tmp_dir, language, code)
                
                # Build and run Docker command
                cmd = self._get_docker_command(language, tmp_dir, code)
                
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=MAX_EXECUTION_TIME,
                )
                
                # Check return code
                if proc.returncode != 0:
                    error_output = proc.stderr.strip() or proc.stdout.strip()
                    return f"[Erreur d'exécution] Code de sortie: {proc.returncode}\n{error_output[:500]}"
                
                # Get output
                output = proc.stdout.strip() or proc.stderr.strip()
                
                # Truncate if too long
                if len(output) > MAX_OUTPUT_BYTES:
                    output = output[:MAX_OUTPUT_BYTES] + "\n... [sortie tronquée]"
                
                return output or "[Exécution terminée sans sortie]"
                
            finally:
                # ALWAYS clean up temp directory
                try:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                except Exception as e:
                    log.error(f"Échec nettoyage du dossier temporaire: {e}")
                    
        except subprocess.TimeoutExpired:
            return f"[Erreur] Timeout d'exécution (> {MAX_EXECUTION_TIME}s)"
        except SecurityError as e:
            return f"[SÉCURITÉ] {str(e)}"
        except Exception as e:
            log.error(f"Erreur exécution code: {e}")
            return f"[Erreur exécution] {str(e)}"

    def execute_safe(self, language: str, code: str) -> dict:
        """
        Execute code with detailed result.
        
        Returns:
            Dict with status, output, error, and security info
        """
        language = language.lower()
        
        # Validate first
        is_valid, error_msg = self.validate_code(language, code)
        
        if not is_valid:
            return {
                "status": "blocked",
                "output": "",
                "error": error_msg,
                "security": "dangerous_pattern",
                "language": language,
            }
        
        if not self.docker_enabled:
            return {
                "status": "error",
                "output": "",
                "error": "Docker non disponible",
                "security": "docker_required",
                "language": language,
            }
        
        # Execute
        output = self.execute(language, code)
        
        # Determine status
        if "[Erreur" in output or "[SÉCURITÉ]" in output:
            status = "error"
        elif not output:
            status = "empty"
        else:
            status = "success"
        
        return {
            "status": status,
            "output": output,
            "error": "" if status == "success" else output,
            "security": "passed",
            "language": language,
        }

