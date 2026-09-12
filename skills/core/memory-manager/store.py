import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional


class MemoryStore:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("memory.json")
        self._memory: dict[str, dict] = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            self._memory = json.loads(self.storage_path.read_text())

    def _save(self):
        self.storage_path.write_text(json.dumps(self._memory, indent=2))

    def store(self, key: str, value: Any, metadata: dict = None) -> bool:
        """Store a key-value pair with metadata"""
        self._memory[key] = {
            "value": value,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        self._save()
        return True


def store(key: str, value: Any, metadata: dict = None) -> bool:
    """Store a key-value pair with metadata"""
    store_instance = MemoryStore()
    return store_instance.store(key, value, metadata)
