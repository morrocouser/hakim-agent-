import json
from pathlib import Path
from typing import Any, Optional


class MemoryRetriever:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("memory.json")
        self._memory: dict[str, dict] = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            self._memory = json.loads(self.storage_path.read_text())

    def retrieve(self, key: str) -> Any:
        """Retrieve a stored value by key"""
        entry = self._memory.get(key)
        if entry:
            return entry.get("value")
        return None


def retrieve(key: str) -> Any:
    """Retrieve a stored value by key"""
    retriever = MemoryRetriever()
    return retriever.retrieve(key)
