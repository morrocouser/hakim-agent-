from axiom.models.memory_models import AxiomMemory, WorkingMemory, EpisodicMemory, SemanticMemory
from datetime import datetime
from typing import Optional
from pathlib import Path
import json
import os


class MemoryManager:
    def __init__(self, storage_path: Optional[str] = None):
        self.memory = AxiomMemory()
        default_dir = Path.home() / ".axiom"
        default_dir.mkdir(parents=True, exist_ok=True)
        self.storage_path = Path(storage_path) if storage_path else default_dir / "memory.json"
        
        # Load from disk if file exists, else init new session
        if not self.load_from_disk():
            self._init_session()

    def _init_session(self):
        now = datetime.now()
        self.memory.working.session_id = f"sess_{now.strftime('%Y%m%d_%H%M%S')}"
        self.memory.working.session_start = now.isoformat()

    def save_to_disk(self) -> bool:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.export(), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def load_from_disk(self) -> bool:
        if not self.storage_path.exists():
            return False
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.load(data)
            return True
        except Exception:
            return False


    def get_working(self) -> WorkingMemory:
        return self.memory.working

    def get_episodic(self) -> EpisodicMemory:
        return self.memory.episodic

    def get_semantic(self) -> SemanticMemory:
        return self.memory.semantic

    def set_current_task(self, task_id: str, description: str, task_type: str,
                         agent: str, model: str, score: float):
        self.memory.working.current_task = {
            "id": task_id,
            "description": description[:120],
            "type": task_type,
            "agent_assigned": agent,
            "model_assigned": model,
            "model_score": score,
            "status": "RUNNING",
            "iteration": 1,
            "quality_score": 0.0,
        }

    def update_task_status(self, status: str, quality_score: Optional[float] = None):
        if self.memory.working.current_task:
            self.memory.working.current_task["status"] = status
            if quality_score is not None:
                self.memory.working.current_task["quality_score"] = quality_score

    def add_active_file(self, path: str, file_type: str):
        self.memory.working.active_files.append({
            "path": path,
            "type": file_type,
            "last_modified": datetime.now().isoformat(),
        })

    def add_to_history(self, task_id: str, resume: str, task_type: str,
                       model: str, outcome: str, artefacts: list[str] = None):
        self.memory.episodic.historique_tâches.append({
            "id": task_id,
            "résumé": resume[:120],
            "type": task_type,
            "modèle": model,
            "outcome": outcome,
            "durée_estimée": "",
            "artefacts": artefacts or [],
            "note_utile": "",
        })
        self.save_to_disk()

    def learn_error(self, code: str, context: str, error: str,
                    correction: str, priority: int):
        self.memory.episodic.erreurs_apprises.append({
            "code": code,
            "contexte": context,
            "erreur": error,
            "correction": correction,
            "score_priorité": priority,
        })
        self.save_to_disk()

    def set_project(self, name: str, project_type: str, description: str,
                    status: str = "En développement", client: str = "Interne"):
        self.memory.semantic.projet = {
            "nom": name,
            "type": project_type,
            "description": description,
            "statut": status,
            "client": client,
        }
        self.save_to_disk()

    def set_stack(self, frontend: str = "", backend: str = "",
                  database: str = "", auth: str = "",
                  infra: str = "", testing: str = "", ci_cd: str = ""):
        self.memory.semantic.stack_technique = {
            "frontend": frontend,
            "backend": backend,
            "base_données": database,
            "auth": auth,
            "infra": infra,
            "testing": testing,
            "ci_cd": ci_cd,
        }
        self.save_to_disk()

    def add_decision(self, decision: str, reason: str, revocable: bool = False):
        self.memory.semantic.décisions_architecturales.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "décision": decision,
            "raison": reason,
            "révocable": revocable,
        })
        self.save_to_disk()


    def add_constraint(self, constraint: str):
        self.memory.semantic.contraintes_projet.append(constraint)

    def get_total_tokens_estimate(self) -> int:
        working_tokens = len(str(self.memory.working.model_dump())) // 4
        episodic_tokens = len(str(self.memory.episodic.model_dump())) // 4
        semantic_tokens = len(str(self.memory.semantic.model_dump())) // 4
        return working_tokens + episodic_tokens + semantic_tokens

    def compress_if_needed(self):
        total = self.get_total_tokens_estimate()
        if total > 3500:
            self._compress_episodic()
            # Tronquer active_files si trop nombreux
            if len(self.memory.working.active_files) > 10:
                self.memory.working.active_files = self.memory.working.active_files[-10:]
            import gc
            gc.collect()

    def _compress_episodic(self):
        history = self.memory.episodic.historique_tâches
        if len(history) > 10:
            old = history[:-10]
            kept = history[-10:]
            for entry in old:
                compressed = f"{entry['id']}: {entry['type']} {entry['outcome']}"
                if entry.get("artefacts"):
                    compressed += f" [{entry['artefacts'][0]}]"
                kept.append({"id": entry['id'], "compressed": compressed})
            self.memory.episodic.historique_tâches = kept

        errors = self.memory.episodic.erreurs_apprises
        self.memory.episodic.erreurs_apprises = [
            e for e in errors if e.get("score_priorité", 0) >= 3
        ]

    def export(self) -> dict:
        return {
            "working": self.memory.working.model_dump(),
            "episodic": self.memory.episodic.model_dump(),
            "semantic": self.memory.semantic.model_dump(),
            "tokens_estimate": self.get_total_tokens_estimate(),
        }

    def load(self, data: dict):
        if "working" in data:
            self.memory.working = WorkingMemory(**data["working"])
        if "episodic" in data:
            self.memory.episodic = EpisodicMemory(**data["episodic"])
        if "semantic" in data:
            self.memory.semantic = SemanticMemory(**data["semantic"])
