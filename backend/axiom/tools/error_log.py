from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class ErrorLogEntry:
    def __init__(self, *, tier: int, agent: str, context: str,
                 symptom: str, root_cause: str, fix: str,
                 lesson: str, score: int = 5):
        self.id = f"E_{uuid.uuid4().hex[:6].upper()}"
        self.tier = tier
        self.agent = agent
        self.context = context
        self.symptom = symptom
        self.root_cause = root_cause
        self.fix = fix
        self.lesson = lesson
        self.score = score
        self.last_occurrence = datetime.now().isoformat()
        self.occurrences = 1

    def to_dict(self):
        return self.__dict__


class ErrorLog:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage = Path(storage_path) if storage_path else Path.home() / ".axiom" / "error_log.jsonl"
        self.storage.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[ErrorLogEntry] = []
        self._load()

    def _load(self):
        if self.storage.exists():
            try:
                with open(self.storage, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self._entries.append(ErrorLogEntry(**json.loads(line)))
            except Exception:
                pass

    def _save(self):
        try:
            with open(self.storage, "w", encoding="utf-8") as f:
                for e in self._entries:
                    f.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
        except Exception:
            pass

    def log(self, *, tier: int, agent: str, context: str,
            symptom: str, root_cause: str, fix: str,
            lesson: str, score: int = 5) -> ErrorLogEntry:
        # Check similar existing entries
        for existing in self._entries:
            if existing.symptom == symptom and existing.context == context:
                existing.last_occurrence = datetime.now().isoformat()
                existing.occurrences += 1
                if score > existing.score:
                    existing.score = score
                self._save()
                return existing
        entry = ErrorLogEntry(
            tier=tier, agent=agent, context=context, symptom=symptom,
            root_cause=root_cause, fix=fix, lesson=lesson, score=score,
        )
        self._entries.append(entry)
        self._save()
        return entry

    def get_lessons(self, context: str = "", min_score: int = 0) -> List[ErrorLogEntry]:
        results = []
        for e in self._entries:
            if e.score >= min_score:
                if not context or context.lower() in e.context.lower():
                    results.append(e)
        return results

    def get_all(self) -> List[ErrorLogEntry]:
        return self._entries.copy()

    def clear(self):
        self._entries.clear()
        self._save()
