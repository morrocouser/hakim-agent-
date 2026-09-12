"""
Security Validator Skill for APEX v4.0

Ce skill fournit des outils de validation de sécurité pour:
- Valider le code avant exécution
- Valider les chemins de fichiers
- Valider le contenu des fichiers
- Détecter les injections

Utilisation:
    from skills.security.security_tools import (
        validate_code,
        validate_file_path,
        validate_file_content,
        scan_for_injections,
        check_dangerous_patterns,
    )
"""

from .security_tools import (
    # Outils de validation
    validate_code,
    validate_file_path,
    validate_file_content,
    scan_for_injections,
    check_dangerous_patterns,
    
    # Versions asynchrones pour le router
    validate_code_async,
    validate_file_path_async,
    validate_file_content_async,
    scan_for_injections_async,
    check_dangerous_patterns_async,
    
    # Alias pour le router de skills
    validate_code_tool,
    validate_file_path_tool,
    validate_file_content_tool,
    scan_for_injections_tool,
    check_dangerous_patterns_tool,
    
    # Modèles Pydantic
    ValidationResult,
    CodeValidationRequest,
    FileValidationRequest,
    
    # Constantes
    SUPPORTED_LANGUAGES,
    DANGEROUS_CODE_PATTERNS,
    INJECTION_PATTERNS,
    DANGEROUS_EXTENSIONS,
    ALLOWED_EXTENSIONS,
    MAX_CODE_LENGTH,
    MAX_FILE_SIZE,
    MAX_FILENAME_LENGTH,
    MAX_PATH_DEPTH,
)

__all__ = [
    # Outils synchrones
    "validate_code",
    "validate_file_path",
    "validate_file_content",
    "scan_for_injections",
    "check_dangerous_patterns",
    
    # Outils asynchrones
    "validate_code_async",
    "validate_file_path_async",
    "validate_file_content_async",
    "scan_for_injections_async",
    "check_dangerous_patterns_async",
    
    # Alias
    "validate_code_tool",
    "validate_file_path_tool",
    "validate_file_content_tool",
    "scan_for_injections_tool",
    "check_dangerous_patterns_tool",
    
    # Modèles
    "ValidationResult",
    "CodeValidationRequest",
    "FileValidationRequest",
    
    # Constantes
    "SUPPORTED_LANGUAGES",
    "DANGEROUS_CODE_PATTERNS",
    "INJECTION_PATTERNS",
    "DANGEROUS_EXTENSIONS",
    "ALLOWED_EXTENSIONS",
    "MAX_CODE_LENGTH",
    "MAX_FILE_SIZE",
    "MAX_FILENAME_LENGTH",
    "MAX_PATH_DEPTH",
]
