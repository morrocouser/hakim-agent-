"""
Input sanitization middleware for AXIOM multi-agent system.

This middleware provides consistent input validation and sanitization
to prevent command injection, XSS, and other injection attacks
across all user inputs in the AXIOM system.

Designed to work with the existing AXIOM architecture while maintaining
the user experience and preserving legitimate user intent.
"""

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
@dataclass
class SanitizationResult:
    """Result of input sanitization with metadata."""
    original: str
    sanitized: str
    was_modified: bool
    warnings: list[str]
    confidence_score: float
class InputSanitizer:
    """
    Comprehensive input sanitizer for AXIOM system.

    Provides multi-layered defense against:
    - Command injection attacks
    - XSS (Cross-Site Scripting)
    - SQL injection patterns
    - Path traversal attacks
    - Code injection attempts
    """

    def __init__(self):
        # Shell metacharacters that enable command execution
        self.shell_metacharacters = [
            '`',  # Backticks - command substitution
            ';',  # Command separator
            '&',  # Background execution
            '|',  # Pipe
            '>',  # Output redirection
            '<',  # Input redirection
            '(',  # Subshell
            ')',  # Subshell
            '{',  # Shell blocks
            '}',  # Shell blocks
            '[',  # Array substitution
            ']',  # Array substitution
            '$',  # Variable expansion
            '\\', # Escape character
        ]

        # Dangerous command patterns
        self.dangerous_commands = [
            r'rm\s+-rf',           # Dangerous file deletion
            r'del\s+/s',           # Windows file deletion
            r'mkfs',               # Filesystem creation
            r'fdisk',              # Disk partitioning
            r'format\s+.*',        # Disk formatting
            r'system\s*\(',       # System commands
            r'exec\s*\(',         # Code execution
            r'eval\s*\(',         # Code evaluation
        ]

        # XSS patterns
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',               # JS protocol
            r'on\w+\s*=',                 # Event handlers
            r'<iframe[^>]*>',             # Iframes
            r'<object[^>]*>',             # Objects
            r'<embed[^>]*>',              # Embeds
            r'expression\s*\(',          # IE expressions
        ]

        # Path traversal patterns
        self.path_traversal_patterns = [
            r'\.\./',                    # Directory traversal
            r'\.\\',                     # Windows directory traversal
            r'/etc/passwd',              # Sensitive files
            r'\\windows\\system32',       # Windows system files
            r'/proc/',                   # Linux proc files
            r'/var/log/',                # Log files
        ]

        # Compiled regex patterns for efficiency
        self.shell_regex = re.compile('|'.join(re.escape(c) for c in self.shell_metacharacters))
        self.dangerous_regex = re.compile('|'.join(self.dangerous_commands), re.IGNORECASE)
        self.xss_regex = re.compile('|'.join(self.xss_patterns), re.IGNORECASE)
        self.traversal_regex = re.compile('|'.join(self.path_traversal_patterns), re.IGNORECASE)

    def sanitize_user_input(self, input_text: str, context: Optional[str] = None) -> SanitizationResult:
        """
        Sanitize user input to prevent injection attacks.

        Args:
            input_text: The user input to sanitize
            context: The context where input is being used (e.g., 'chat', 'command', 'search')

        Returns:
            SanitizationResult with original, sanitized, modification flag, warnings, and confidence score
        """
        if not input_text or not input_text.strip():
            return SanitizationResult(
                original=input_text or "",
                sanitized="",
                was_modified=False,
                warnings=["Empty input"],
                confidence_score=1.0
            )

        original = input_text.strip()
        sanitized = original
        warnings = []
        modification_count = 0

        # Apply different sanitization levels based on context
        if context == 'high_security':
            # Maximum security for sensitive operations
            sanitized = self._apply_high_security_sanitization(sanitized, warnings)
            modification_count += self._count_modifications(original, sanitized)
        elif context == 'medium_security':
            # Standard security for most user interactions
            sanitized = self._apply_medium_security_sanitization(sanitized, warnings)
            modification_count += self._count_modifications(original, sanitized)
        else:
            # Basic security for less sensitive operations
            sanitized = self._apply_basic_security_sanitization(sanitized, warnings)
            modification_count += self._count_modifications(original, sanitized)

        # Calculate confidence score
        confidence = self._calculate_confidence_score(original, sanitized, warnings)

        return SanitizationResult(
            original=original,
            sanitized=sanitized,
            was_modified=modification_count > 0,
            warnings=warnings,
            confidence_score=confidence
        )

    def _apply_high_security_sanitization(self, text: str, warnings: list[str]) -> str:
        """Apply maximum security sanitization."""
        # Remove all shell metacharacters
        text = self.shell_regex.sub(' ', text)

        # Remove dangerous command patterns
        text = self.dangerous_regex.sub(' ', text)

        # Remove XSS patterns
        text = self.xss_regex.sub(' ', text)

        # Remove path traversal patterns
        text = self.traversal_regex.sub(' ', text)

        # Remove potential SQL injection patterns
        text = self._remove_sql_injection_patterns(text)

        # Remove code injection patterns (only for high security context)
        text = self._remove_code_injection_patterns(text)

        # Remove special Unicode characters that could be exploited
        text = self._remove_exploitable_unicode(text)

        # Remove excessive whitespace (could be used for evasion)
        text = re.sub(r'\s+', ' ', text).strip()

        # If text becomes too short, treat as empty
        if len(text) < 3:
            warnings.append("Input too short after security sanitization")
            return ""

        return text

    def _apply_medium_security_sanitization(self, text: str, warnings: list[str]) -> str:
        """Apply standard security sanitization."""
        # Remove shell metacharacters
        text = self.shell_regex.sub(' ', text)

        # Remove dangerous command patterns
        text = self.dangerous_regex.sub(' ', text)

        # Remove XSS patterns
        text = self.xss_regex.sub(' ', text)

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _apply_basic_security_sanitization(self, text: str, warnings: list[str]) -> str:
        """Apply basic security sanitization."""
        # Remove obvious command injection patterns
        text = re.sub(r'[;&|`$()>{}[\]\']', ' ', text)

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _remove_sql_injection_patterns(self, text: str) -> str:
        """Remove SQL injection patterns."""
        sql_patterns = [
            r'union\s+select',     # Union-based SQL injection
            r'drop\s+table',       # Drop table
            r'insert\s+into',      # Insert statements
            r'update\s+set',       # Update statements
            r'delete\s+from',      # Delete statements
            r'--\s.*',            # SQL comments
            r'/\*.*\*/',          # SQL block comments
            r'\bor\s+1\s*=\s*1',   # Always true condition
            r'\sand\s+1\s*=\s*1', # Always true conjunction
            r'exec\s+\(',         # Execute function
            r'sp_\w+',            # System procedure
        ]

        for pattern in sql_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)

        return text

    def _remove_code_injection_patterns(self, text: str) -> str:
        """Remove code injection patterns."""
        code_patterns = [
            r'python\s+',         # Python code indicators
            r'javascript\s+',    # JavaScript indicators
            r'<\?php',           # PHP opening tag
            r'<%',               # ASP opening tag
            r'raise\s+Exception', # Exception raising
            r'import\s+',        # Import statements
            r'from\s+.*\s+import', # Import statements
            r'def\s+\w+',         # Function definitions
            r'class\s+\w+',       # Class definitions
        ]

        for pattern in code_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)

        return text

    def _remove_exploitable_unicode(self, text: str) -> str:
        """Remove Unicode characters that could be exploited for evasion."""
        # Remove Unicode bidirectional characters (can be used for obfuscation)
        text = re.sub(r'[‪-‮⁦-⁩]', ' ', text)

        # Remove zero-width characters
        text = re.sub(r'[​-‍﻿]', ' ', text)

        # Remove confusable characters
        text = re.sub(r'[͵־׀ׄ؜ٟ٪٫ۖۗۮۯۿ࠰-࠶aࡁ࢒-ࢬॐ-ॕ॰-ঃਕ੠ੱ઺-ૅૢ-ೳെ-ൡัັິີ໙]', ' ', text)

        return text

    def _count_modifications(self, original: str, sanitized: str) -> int:
        """Count the number of modifications made."""
        if original == sanitized:
            return 0

        # Simple count based on character differences
        modification_score = abs(len(original) - len(sanitized))

        # Increase score for removed special characters
        removed_special = sum(1 for c in original if c in self.shell_metacharacters and c not in sanitized)
        modification_score += removed_special * 2

        # Increase score for removed command patterns
        for pattern in self.dangerous_commands:
            matches = len(re.findall(pattern, original, re.IGNORECASE))
            modification_score += matches * 3

        return modification_score

    def _calculate_confidence_score(self, original: str, sanitized: str, warnings: list[str]) -> float:
        """Calculate confidence score for sanitization."""
        # Start with base score
        confidence = 1.0

        # Reduce confidence for warnings
        warning_penalty = min(len(warnings) * 0.1, 0.5)
        confidence -= warning_penalty

        # Reduce confidence if original was modified significantly
        modification_ratio = len(sanitized) / max(len(original), 1)
        if modification_ratio < 0.3:
            confidence *= 0.7  # Significantly modified content
        elif modification_ratio > 0.9:
            confidence *= 0.9  # Slightly modified

        # Ensure confidence is within bounds
        return max(0.0, min(1.0, confidence))

    def validate_sanitized_input(self, original: str, sanitized: str, context: str = "general") -> tuple[bool, list[str]]:
        """
        Validate that sanitized input meets security requirements.

        Args:
            original: Original unsanitized input
            sanitized: Sanitized input
            context: Context of use

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for empty results
        if not sanitized.strip():
            issues.append("Input was sanitized to empty string")

        # Check for very short results (could be evasive)
        if len(sanitized) < 2:
            issues.append("Sanitized input is too short")

        # Check for repeated whitespace (could indicate evasion)
        if '  ' in sanitized.replace('\n', ' '):
            issues.append("Input contains excessive whitespace")

        # Check for removed special characters that should be legitimate
        if context == "code_discussion":
            # In technical contexts, some special chars might be legitimate
            legitimate_chars = {'<', '>', '&', '|', ';', '(', ')', '{', '}', '+', '-', '*', '/', '=', '!', '?', '@', '#', '%', '^', '~', '`'}
            removed_legitimate = sum(1 for c in original if c in legitimate_chars and c not in sanitized)
            if removed_legitimate > 3:  # Significant removal of legitimate technical chars
                issues.append(f"Removed {removed_legitimate} potentially legitimate technical characters")

        # Security-specific checks
        if context == "high_security":
            # Check for remaining dangerous patterns
            if any(re.search(pattern, sanitized, re.IGNORECASE) for pattern in self.dangerous_commands):
                issues.append("Remaining dangerous command patterns")

            if self.xss_regex.search(sanitized):
                issues.append("Remaining XSS patterns")

            if self.traversal_regex.search(sanitized):
                issues.append("Remaining path traversal patterns")

        is_valid = len(issues) == 0
        return is_valid, issues

    def get_sanitization_summary(self, result: SanitizationResult) -> str:
        """Get a human-readable summary of sanitization."""
        if not result.was_modified:
            return "Input approved with standard sanitization"

        summary_parts = []

        # Add modification info
        if result.was_modified:
            original_words = len(result.original.split())
            sanitized_words = len(result.sanitized.split())
            if sanitized_words < original_words * 0.5:
                summary_parts.append("Content was significantly modified")
            else:
                summary_parts.append("Input was sanitized for security")

        # Add warnings
        if result.warnings:
            summary_parts.extend(result.warnings)

        # Add confidence
        if result.confidence_score < 0.5:
            summary_parts.append("Low confidence in sanitization")
        elif result.confidence_score < 0.8:
            summary_parts.append("Medium confidence in sanitization")
        else:
            summary_parts.append("High confidence in sanitization")

        return ", ".join(summary_parts)

# Global sanitizer instance for backward compatibility
_global_sanitizer = InputSanitizer()
def sanitize_input(input_text: str, context: Optional[str] = None) -> SanitizationResult:
    """Global convenience function for input sanitization."""
    return _global_sanitizer.sanitize_user_input(input_text, context)
def validate_sanitized_input(original: str, sanitized: str, context: str = "general") -> tuple[bool, list[str]]:
    """Global validation convenience function."""
    return _global_sanitizer.validate_sanitized_input(original, sanitized, context)
# Export commonly used functions
__all__ = [
    'InputSanitizer',
    'SanitizationResult',
    'sanitize_input',
    'validate_sanitized_input',
]