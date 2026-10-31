"""
HakimAgent - Mémoire et Sauvegarde Locale (Étape 5)

Ce module fournit un moteur de persistance local (SQLite + JSON) permettant
d'enregistrer l'état partagé de l'agent après chaque tour d'exécution.
Il permet de reprendre une session interrompue sans réexécuter les étapes validées.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from hakim_agent.state import AgentState, AgentStatus


class SessionStorage:
    """
    Gestionnaire de persistance locale basé sur SQLite avec export/import JSON.
    Garantit l'atomicité des sauvegardes après chaque étape.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent / "data"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "hakim_sessions.db")
        else:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self.db_path = db_path

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_prompt TEXT NOT NULL,
                    status TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    current_step INTEGER NOT NULL,
                    context_json TEXT NOT NULL,
                    history_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    metadata_json TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    step_name TEXT NOT NULL,
                    result_json TEXT,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
                """
            )
            conn.commit()

    def save_checkpoint(
        self,
        state: AgentState,
        step_name: Optional[str] = None,
        step_result: Optional[Any] = None,
    ) -> None:
        """Sauvegarde ou met à jour l'état de la session et ajoute un checkpoint."""
        now = time.time()
        state["updated_at"] = now

        plan_json = json.dumps(state.get("plan", []), ensure_ascii=False)
        context_json = json.dumps(state.get("context", {}), ensure_ascii=False, default=str)
        history_json = json.dumps(state.get("history", []), ensure_ascii=False, default=str)
        metadata_json = json.dumps(state.get("metadata", {}), ensure_ascii=False, default=str)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (
                    session_id, user_prompt, status, plan_json, current_step,
                    context_json, history_json, created_at, updated_at, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    status=excluded.status,
                    plan_json=excluded.plan_json,
                    current_step=excluded.current_step,
                    context_json=excluded.context_json,
                    history_json=excluded.history_json,
                    updated_at=excluded.updated_at,
                    metadata_json=excluded.metadata_json
                """,
                (
                    state["session_id"],
                    state.get("user_prompt", ""),
                    state.get("status", AgentStatus.RUNNING.value),
                    plan_json,
                    int(state.get("current_step", 0)),
                    context_json,
                    history_json,
                    float(state.get("created_at", now)),
                    now,
                    metadata_json,
                ),
            )

            if step_name is not None:
                res_json = json.dumps(step_result, ensure_ascii=False, default=str) if step_result is not None else None
                cursor.execute(
                    """
                    INSERT INTO checkpoints (session_id, step_index, step_name, result_json, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (state["session_id"], state.get("current_step", 0), step_name, res_json, now),
                )

            conn.commit()

    def load_session(self, session_id: str) -> Optional[AgentState]:
        """Charge l'état complet d'une session depuis SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return AgentState(
                session_id=row["session_id"],
                user_prompt=row["user_prompt"],
                status=row["status"],
                plan=json.loads(row["plan_json"]),
                current_step=row["current_step"],
                context=json.loads(row["context_json"]),
                history=json.loads(row["history_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=json.loads(row["metadata_json"] or "{}"),
            )

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Liste les sessions récentes enregistrées."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT session_id, user_prompt, status, current_step, created_at, updated_at
                FROM sessions
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_session(self, session_id: str) -> bool:
        """Supprime une session et ses checkpoints associés."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checkpoints WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0

    def export_json(self, session_id: str, filepath: str) -> bool:
        """Exporte l'état d'une session dans un fichier JSON."""
        state = self.load_session(session_id)
        if not state:
            return False
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        return True

    def import_json(self, filepath: str) -> Optional[AgentState]:
        """Importe un état de session depuis un fichier JSON et le synchronise dans SQLite."""
        path = Path(filepath)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            state: AgentState = json.load(f)
        self.save_checkpoint(state)
        return state
