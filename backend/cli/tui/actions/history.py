import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, asdict


@dataclass
class HistoryEntry:
    timestamp: str
    role: str
    content: str
    agent: Optional[str] = None
    model: Optional[str] = None
    score: Optional[float] = None
    quality: Optional[float] = None


class HistoryManager:
    def __init__(self, history_file: str):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[HistoryEntry] = []
        self._load()

    def _load(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self._entries.append(HistoryEntry(**json.loads(line)))
            except Exception:
                pass

    def add(self, entry: HistoryEntry):
        self._entries.append(entry)
        # Keep only last N entries
        from cli.tui.config import CONFIG
        max_hist = CONFIG.max_history
        if len(self._entries) > max_hist:
            self._entries = self._entries[-max_hist:]
        self._save()

    def _save(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                for entry in self._entries:
                    f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        except Exception:
            pass

    def get_all(self) -> List[HistoryEntry]:
        return self._entries.copy()

    def get_user_messages(self) -> List[str]:
        return [e.content for e in self._entries if e.role == "user"]

    def clear(self):
        self._entries.clear()
        self._save()