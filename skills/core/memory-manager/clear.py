import json
from pathlib import Path
from typing import Optional
import fnmatch


class MemoryClearer:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("memory.json")
        self._memory: dict[str, dict] = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            self._memory = json.loads(self.storage_path.read_text())

    def _save(self):
        self.storage_path.write_text(json.dumps(self._memory, indent=2))

    def clear(self, pattern: str) -> bool:
        """Clear memory entries matching pattern"""
        keys_to_remove = []

        for key in self._memory.keys():
            if fnmatch.fnmatch(key, pattern):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._memory[key]

        if keys_to_remove:
            self._save()

        return len(keys_to_remove) > 0


def clear(pattern: str) -> bool:
    """Clear memory entries matching pattern"""
    clearer = MemoryClearer()
    return clearer.clear(pattern)
