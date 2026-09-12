import json
from pathlib import Path
from typing import Any, Optional


class MemorySearcher:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("memory.json")
        self._memory: dict[str, dict] = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            self._memory = json.loads(self.storage_path.read_text())

    def search(self, query: str) -> list[dict]:
        """Search memory for entries matching query"""
        results = []
        query_lower = query.lower()

        for key, entry in self._memory.items():
            # Search in key
            if query_lower in key.lower():
                results.append({"key": key, **entry})
                continue

            # Search in value (if string)
            value = entry.get("value")
            if isinstance(value, str) and query_lower in value.lower():
                results.append({"key": key, **entry})
                continue

            # Search in metadata
            metadata = entry.get("metadata", {})
            for meta_key, meta_value in metadata.items():
                if isinstance(meta_value, str) and query_lower in meta_value.lower():
                    results.append({"key": key, **entry})
                    break

        return results


def search(query: str) -> list[dict]:
    """Search memory for entries matching query"""
    searcher = MemorySearcher()
    return searcher.search(query)
