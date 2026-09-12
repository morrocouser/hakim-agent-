"""
Security Tools for APEX v4.0

Cette module fournit des outils de validation de sécurité 
qui peuvent être utilisés par le système de skills ou directement.

AUTREFOIS: Ces outils ne font QUE de la validation, ils n'exécutent PAS de code.
"""

import re
from typing import Optional, Tuple, List, Dict, Any
from pydantic import BaseModel, Field
from axiom.logging_setup import log


# =============================================================================
# CONFIGURATION DE SÉCURITÉ
# =============================================================================

# Langages supportés pour la validation
SUPPORTED_LANGUAGES = {"python", "javascript", "bash", "sql"}

# Patterns dangereux par langage
DANGEROUS_CODE_PATTERNS: Dict[str, List[str]] = {
    "python": [
        # Accès système
        r"import\s+os",
        r"import\s+subprocess",
        r"import\s+sys",
        r"import\s+shutil",
        r"import\s+socket",
        r"import\s+requests",
        r"import\s+httpx",
        r"import\s+urllib",
        r"import\s+ftplib",
        r"import\s+pickle",
        r"import\s+marshal",
        r"import\s+ctypes",
        r"import\s+multiprocessing",
        r"import\s+threading",
        r"import\s+signal",
        r"import\s+atexit",
        r"import\s+gc",
        r"import\s+inspect",
        # Accès fichiers
        r"open\(",
        r"file\(",
        # Exécution de code
        r"exec\s*\(",
        r"eval\s*\(",
        r"compile\s*\(",
        r"__import__\s*\(",
        # Appels système
        r"os\.",
        r"subprocess\.",
        r"sys\.",
        r"shutil\.",
        r"socket\.",
        # Autre
        r"input\s*\(",
        r"breakpoint\s*\(",
        r"pdb\.",
        r"webbrowser\.",
    ],
    "javascript": [
        # Require dangereux
        r"require\s*\(\s*['\"]child_process['\"]",
        r"require\s*\(\s*['\"]fs['\"]",
        r"require\s*\(\s*['\"]http['\"]",
        r"require\s*\(\s*['\"]https['\"]",
        r"require\s*\(\s*['\"]net['\"]",
        r"require\s*\(\s*['\"]dgram['\"]",
        r"require\s*\(\s*['\"]os['\"]",
        r"require\s*\(\s*['\"]process['\"]",
        # Évaluation de code
        r"eval\s*\(",
        r"Function\s*\(",
        r"new\s+Function\s*\(",
        r"\.exec",
        r"\.spawn",
        r"\.execFile",
        r"\.fork",
        # Accès DOM dangereux
        r"document\.write",
        r"window\.open",
        r"location\.",
        # WebSocket
        r"WebSocket\s*\(",
        r"new\s+WebSocket\s*\(",
    ],
    "bash": [
        # Commandes dangereuses
        r"rm\s+-rf",
        r"dd\s+if=",
        r"mkfs",
        r"chmod\s+777",
        r"chown",
        r"wget\s+http",
        r"curl\s+http",
        r"nc\s+-",
        r"netcat",
        r"nmap",
        r"ssh",
        r"scp",
        r"sftp",
        r"sudo",
        r"su\s+-",
        r"passwd",
        r"export\s+",
        r"source\s+",
        r"\.\s*/",
        # Redirections
        r">\s*/",
        r">>\s*/",
        r"2>\s*/",
        # Pipes
        r"\|\s*rm",
        r"\|\s*dd",
        r"\|\s*:",
        # Command substitution
        r"`.*`",
        r"\$\(",
    ],
    "sql": [
        # SQL Injection patterns
        r"--\s*$",
        r"#\s*$",
        r";\s*DROP",
        r";\s*DELETE",
        r";\s*TRUNCATE",
        r";\s*INSERT",
        r";\s*UPDATE",
        r";\s*SELECT\s*.*FROM",
        r"UNION\s+SELECT",
        r"EXEC\s*\(",
        r"EXECUTE\s*\(",
        r"xp_cmdshell",
        r"LOAD_FILE",
        r"INTO\s+OUTFILE",
        r"INTO\s+DUMPFILE",
        r"BENCHMARK\s*\(",
        r"SLEEP\s*\(",
        # Bool-based blind
        r"OR\s+1=1",
        r"OR\s+'[^']*'='[^']*'",
        r"AND\s+1=2",
        # Time-based blind
        r"IF\s*\(",
        r"CASE\s+WHEN",
    ],
}

# Patterns d'injection génériques
INJECTION_PATTERNS: List[Tuple[str, str]] = [
    (r"(?:--|#|/\*|\*/|;)\s*", "SQL/Command comment or separator"),
    (r"(?:SELECT|INSERT|UPDATE|DELETE|DROP)\s+.*\s+FROM\s+", "SQL query"),
    (r"(?:rm|cp|mv|dd|wget|curl)\s+[\w/.-]+\s*", "Command injection"),
    (r"(?:<script|javascript:|onerror=|onload=)", "XSS"),
    (r"(?:<?php|<%|<%=|%>|<?|?>)", "PHP code injection"),
    (r"(?:\b(?:eval|exec|system|passthru|shell_exec)\b)", "Code execution function"),
    (r"(?:\$\(|`[^`]+`)", "Command substitution"),
    (r"(?:1=1|'='|\"=\")", "SQL tautology"),
]

# Extensions de fichiers dangereuses
DANGEROUS_EXTENSIONS = {
    ".sh", ".bash", ".zsh", ".fish",
    ".bat", ".cmd", ".ps1", ".psm1",
    ".exe", ".dll", ".so", ".com", ".msi",
    ".app", ".jar", ".class", ".war", ".ear",
    ".js", ".jsx", ".ts", ".tsx",  # Peut être dangereux
    ".vbs", ".vbe", ".wsf", ".wsc",
}

# Extensions de fichiers autorisées
ALLOWED_EXTENSIONS = {
    ".py", ".pyc", ".pyw",
    ".md", ".txt", ".csv",
    ".json", ".yaml", ".yml",
    ".xml", ".html", ".htm",
    ".css", ".scss", ".sass",
    ".sql", ".db",
    ".pdf", ".doc", ".docx",
    ".xls", ".xlsx", ".ppt", ".pptx",
}

# Limites
MAX_CODE_LENGTH = 50_000  # 50KB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILENAME_LENGTH = 255
MAX_PATH_DEPTH = 10


# =============================================================================
# MODÈLES PYDANTIC
# =============================================================================

class ValidationResult(BaseModel):
    """Résultat d'une validation de sécurité."""
    valid: bool = Field(..., description="Indique si la validation a réussi")
    errors: List[str] = Field(default_factory=list, description="Liste des erreurs")
    warnings: List[str] = Field(default_factory=list, description="Liste des avertissements")
    score: float = Field(default=100.0, description="Score de sécurité (0-100)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Détails supplémentaires")


class CodeValidationRequest(BaseModel):
    """Requête de validation de code."""
    code: str = Field(..., description="Code source à valider")
    language: str = Field(default="python", description="Langage du code")
    strict: bool = Field(default=True, description="Mode strict (bloque les avertissements)")


class FileValidationRequest(BaseModel):
    """Requête de validation de fichier."""
    path: str = Field(..., description="Chemin du fichier")
    content: Optional[str] = Field(default=None, description="Contenu du fichier (optionnel)")
    operation: str = Field(default="create", description="Opération (create, read, delete)")


# =============================================================================
# OUTILS DE VALIDATION
# =============================================================================

def validate_code(code: str, language: str = "python", strict: bool = True) -> ValidationResult:
    """
    Valider du code source contre les patterns dangereux.
    
    Args:
        code: Code source à valider
        language: Langage du code
        strict: Si True, les avertissements deviennent des erreurs
    
    Returns:
        ValidationResult avec les erreurs et avertissements
    """
    language = language.lower()
    result = ValidationResult(valid=True, score=100.0)
    
    # Vérifier le langage
    if language not in SUPPORTED_LANGUAGES:
        result.valid = False
        result.errors.append(f"Langage non supporté: {language}")
        result.score = 0.0
        return result
    
    # Vérifier la longueur
    if len(code) > MAX_CODE_LENGTH:
        result.valid = False
        result.errors.append(f"Code trop long: {len(code)} > {MAX_CODE_LENGTH}")
        result.score -= 50.0
    
    # Vérifier les patterns spécifiques au langage
    patterns = DANGEROUS_CODE_PATTERNS.get(language, [])
    for pattern in patterns:
        if re.search(pattern, code, re.IGNORECASE):
            result.valid = False
            result.errors.append(f"Pattern dangereux détecté: {pattern[:50]}")
            result.score -= 20.0
    
    # Vérifier les patterns d'injection génériques
    for pattern, description in INJECTION_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            result.warnings.append(f"Pattern d'injection détecté: {description}")
            result.score -= 10.0
    
    # En mode strict, les avertissements deviennent des erreurs
    if strict and result.warnings:
        result.valid = False
        result.errors.extend(result.warnings)
        result.warnings = []
    
    # Clamper le score
    result.score = max(0.0, min(100.0, result.score))
    
    # Ajouter des détails
    result.details = {
        "language": language,
        "length": len(code),
        "checked_patterns": len(patterns),
    }
    
    return result


def validate_file_path(path: str, operation: str = "create") -> ValidationResult:
    """
    Valider un chemin de fichier contre les attaques.
    
    Args:
        path: Chemin à valider
        operation: Opération effectuée (create, read, delete)
    
    Returns:
        ValidationResult
    """
    result = ValidationResult(valid=True, score=100.0)
    
    # Vérifier la longueur
    if len(path) > MAX_FILENAME_LENGTH:
        result.valid = False
        result.errors.append(f"Chemin trop long: {len(path)} > {MAX_FILENAME_LENGTH}")
        result.score -= 30.0
    
    # Vérifier les patterns dangereux
    for pattern, description in INJECTION_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            result.valid = False
            result.errors.append(f"Chemin dangereux: {description}")
            result.score -= 20.0
    
    # Détecter le path traversal
    if ".." in path or path.startswith("/") or path.startswith("\\"):
        result.valid = False
        result.errors.append("Tentative de path traversal détectée")
        result.score -= 50.0
    
    # Vérifier la profondeur du chemin
    depth = path.count("/") + path.count("\\")
    if depth > MAX_PATH_DEPTH:
        result.valid = False
        result.errors.append(f"Chemin trop profond: {depth} > {MAX_PATH_DEPTH}")
        result.score -= 20.0
    
    # Vérifier l'extension
    ext = Path(path).suffix.lower()
    if ext in DANGEROUS_EXTENSIONS:
        result.valid = False
        result.errors.append(f"Extension dangereuse: {ext}")
        result.score -= 40.0
    elif ext not in ALLOWED_EXTENSIONS and ext:
        result.warnings.append(f"Extension non autorisée: {ext}")
        result.score -= 10.0
    
    # Clamper le score
    result.score = max(0.0, min(100.0, result.score))
    
    # Ajouter des détails
    result.details = {
        "operation": operation,
        "path": path,
        "extension": ext,
        "depth": depth,
    }
    
    return result


def validate_file_content(content: str, filename: Optional[str] = None) -> ValidationResult:
    """
    Valider le contenu d'un fichier.
    
    Args:
        content: Contenu à valider
        filename: Nom du fichier (optionnel, pour vérifier l'extension)
    
    Returns:
        ValidationResult
    """
    result = ValidationResult(valid=True, score=100.0)
    
    # Vérifier la taille
    content_bytes = len(content.encode("utf-8", errors="ignore"))
    if content_bytes > MAX_FILE_SIZE:
        result.valid = False
        result.errors.append(f"Contenu trop grand: {content_bytes} > {MAX_FILE_SIZE}")
        result.score -= 50.0
    
    # Vérifier que c'est du texte valide
    try:
        content.encode("utf-8")
    except UnicodeEncodeError:
        result.valid = False
        result.errors.append("Contenu non-UTF-8 détecté")
        result.score -= 30.0
    
    # Vérifier les patterns d'injection
    for pattern, description in INJECTION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            result.warnings.append(f"Pattern d'injection détecté: {description}")
            result.score -= 15.0
    
    # Vérifier par rapport au nom de fichier
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in DANGEROUS_EXTENSIONS:
            result.valid = False
            result.errors.append(f"Extension dangereuse pour le contenu: {ext}")
            result.score -= 40.0
    
    # Clamper le score
    result.score = max(0.0, min(100.0, result.score))
    
    # Ajouter des détails
    result.details = {
        "size": content_bytes,
        "filename": filename,
        "checked_patterns": len(INJECTION_PATTERNS),
    }
    
    return result


def scan_for_injections(text: str, context: Optional[str] = None) -> ValidationResult:
    """
    Scanner un texte pour les injections de code ou SQL.
    
    Args:
        text: Texte à scanner
        context: Contexte (ex: "sql", "javascript", "python")
    
    Returns:
        ValidationResult avec les injections détectées
    """
    result = ValidationResult(valid=True, score=100.0)
    
    # Utiliser tous les patterns d'injection
    all_patterns = INJECTION_PATTERNS
    if context and context.lower() in DANGEROUS_CODE_PATTERNS:
        all_patterns.extend(
            (p, f"{context} pattern") for p in DANGEROUS_CODE_PATTERNS[context.lower()]
        )
    
    for pattern, description in all_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result.warnings.append(f"Injection détectée: {description} ({len(matches)} occurrences)")
            result.score -= 10.0 * len(matches)
    
    # Si des injections ont été détectées, marquer comme invalide
    if result.warnings:
        result.valid = False
        result.errors.extend(result.warnings)
        result.warnings = []
    
    # Clamper le score
    result.score = max(0.0, min(100.0, result.score))
    
    # Ajouter des détails
    result.details = {
        "context": context,
        "scanned_length": len(text),
        "patterns_checked": len(all_patterns),
    }
    
    return result


def check_dangerous_patterns(
    text: str,
    patterns: Optional[List[str]] = None,
    context: Optional[str] = None
) -> ValidationResult:
    """
    Vérifier un texte contre des patterns dangereux personnalisés.
    
    Args:
        text: Texte à vérifier
        patterns: Liste de patterns regex (optionnel)
        context: Contexte pour des patterns prédéfinis
    
    Returns:
        ValidationResult
    """
    result = ValidationResult(valid=True, score=100.0)
    
    # Utiliser les patterns par défaut si aucun fourni
    if patterns is None:
        if context and context.lower() in DANGEROUS_CODE_PATTERNS:
            patterns = DANGEROUS_CODE_PATTERNS[context.lower()]
        else:
            patterns = []
    
    # Vérifier chaque pattern
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            result.valid = False
            result.errors.append(f"Pattern correspondant: {pattern[:50]}")
            result.score -= 20.0
    
    # Clamper le score
    result.score = max(0.0, min(100.0, result.score))
    
    # Ajouter des détails
    result.details = {
        "context": context,
        "patterns_checked": len(patterns),
        "matches": len(result.errors),
    }
    
    return result


# =============================================================================
# OUTILS ASYNCHRONES (pour compatibilité avec le router de skills)
# =============================================================================

async def validate_code_async(
    code: str,
    language: str = "python",
    strict: bool = True
) -> dict:
    """Version asynchrone de validate_code pour le système de skills."""
    result = validate_code(code, language, strict)
    return result.model_dump()


async def validate_file_path_async(
    path: str,
    operation: str = "create"
) -> dict:
    """Version asynchrone de validate_file_path pour le système de skills."""
    result = validate_file_path(path, operation)
    return result.model_dump()


async def validate_file_content_async(
    content: str,
    filename: Optional[str] = None
) -> dict:
    """Version asynchrone de validate_file_content pour le système de skills."""
    result = validate_file_content(content, filename)
    return result.model_dump()


async def scan_for_injections_async(
    text: str,
    context: Optional[str] = None
) -> dict:
    """Version asynchrone de scan_for_injections pour le système de skills."""
    result = scan_for_injections(text, context)
    return result.model_dump()


async def check_dangerous_patterns_async(
    text: str,
    patterns: Optional[List[str]] = None,
    context: Optional[str] = None
) -> dict:
    """Version asynchrone de check_dangerous_patterns pour le système de skills."""
    result = check_dangerous_patterns(text, patterns, context)
    return result.model_dump()


# Alias pour le router de skills
validate_code_tool = validate_code_async
validate_file_path_tool = validate_file_path_async
validate_file_content_tool = validate_file_content_async
scan_for_injections_tool = scan_for_injections_async
check_dangerous_patterns_tool = check_dangerous_patterns_async
