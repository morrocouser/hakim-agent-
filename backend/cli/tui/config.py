import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import stat


@dataclass
class AxiomConfig:
    api_base_url: str = "http://localhost:8000/api/v1"
    openrouter_api_key: str = ""
    theme: str = "dark"
    compact_mode: bool = True
    show_timestamps: bool = True
    max_history: int = 1000
    auto_scroll: bool = True
    streaming_enabled: bool = True
    default_agent: str = ""
    default_model: str = ""
    history_file: str = ""


CONFIG = AxiomConfig()


def validate_api_key(api_key: str):
    """Validate OpenRouter API key format."""
    if not api_key or not api_key.strip():
        raise ValueError("API key is empty")
    if api_key == "test-key-placeholder":
        return  # Allow placeholder for testing
    if not api_key.startswith("sk-or-"):
        raise ValueError("Invalid OpenRouter API key format (should start with 'sk-or-')")


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

    # Override from env
    env_key = os.getenv("OPENROUTER_API_KEY")
    if env_key:
        CONFIG.openrouter_api_key = env_key
    elif not CONFIG.openrouter_api_key:
        # Allow running without API key for testing (will fail on actual API calls)
        CONFIG.openrouter_api_key = "test-key-placeholder"
        print("Warning: OPENROUTER_API_KEY not set. Using placeholder. API calls will fail.")

    env_url = os.getenv("AXIOM_API_URL")
    if env_url:
        CONFIG.api_base_url = env_url
    elif not CONFIG.api_base_url.startswith("http"):
        raise ValueError("AXIOM_API_URL not valid or not set in config")

    # Sanitize config values
    CONFIG.api_base_url = CONFIG.api_base_url.strip()
    CONFIG.openrouter_api_key = CONFIG.openrouter_api_key.strip()

    # Validate API key format
    try:
        validate_api_key(CONFIG.openrouter_api_key)
    except ValueError as e:
        if env_key:
            # If from env, just warn but don't fail
            print(f"Warning: {e}")
        else:
            raise


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
        try:
            os.chmod(config_file, stat.S_IRUSR | stat.S_IWUSR)
            config_dir.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass
    except Exception:
        pass