import json
from datetime import datetime
from pathlib import Path
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
    def __init__(self, path: str = ""):
        if not path:
            path = str(Path.home() / ".axiom" / "history.jsonl")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[HistoryEntry] = []
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self._entries.append(HistoryEntry(**json.loads(line)))
            except Exception:
                pass

    def add(self, entry: HistoryEntry):
        if not entry.timestamp:
            entry.timestamp = datetime.now().isoformat()
        self._entries.append(entry)
        if len(self._entries) > 500:
            self._entries = self._entries[-500:]
        self._save()

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                for e in self._entries:
                    f.write(json.dumps(asdict(e), ensure_ascii=False) + "\n")
        except Exception:
            pass

    def get_user_messages(self) -> List[str]:
        return [e.content for e in self._entries if e.role == "user"]

    def clear(self):
        self._entries.clear()
        self._save()
