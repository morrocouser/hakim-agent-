"""
HakimAgent - State partagé et Bus d'événements (Étape 1)

Ce module implémente le modèle d'état unifié inspiré de LangGraph et le bus
d'événements asynchrone pour la communication temps réel (UI/CLI/Logs).
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypedDict


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class EventType(str, Enum):
    PIPELINE_START = "pipeline_start"
    PLAN_CREATED = "plan_created"
    STEP_START = "step_start"
    STEP_ROUTED = "step_routed"
    WORKER_START = "worker_start"
    WORKER_OUTPUT = "worker_output"
    REVIEW_START = "review_start"
    REVIEW_RESULT = "review_result"
    CORRECTION_START = "correction_start"
    CORRECTION_RESULT = "correction_result"
    STEP_FINISH = "step_finish"
    PIPELINE_FINISH = "pipeline_finish"
    CHECKPOINT_SAVED = "checkpoint_saved"
    ERROR = "error"


class AgentState(TypedDict, total=False):
    """
    Format standard partagé de l'état de HakimAgent (style LangGraph StateGraph).
    Chaque sous-agent reçoit cet objet, lit le contexte et y inscrit ses résultats.
    """
    session_id: str
    user_prompt: str
    plan: List[str]
    current_step: int
    context: Dict[str, Any]
    history: List[Dict[str, Any]]
    status: str
    created_at: float
    updated_at: float
    metadata: Dict[str, Any]


def create_initial_state(prompt: str, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> AgentState:
    """Initialise un nouvel état standard pour une session HakimAgent."""
    now = time.time()
    return AgentState(
        session_id=session_id or f"session_{uuid.uuid4().hex[:10]}",
        user_prompt=prompt,
        plan=[],
        current_step=0,
        context={},
        history=[],
        status=AgentStatus.PENDING.value,
        created_at=now,
        updated_at=now,
        metadata=metadata or {},
    )


class AgentEvent:
    """Représente un événement émis pendant le cycle de vie du pipeline."""

    def __init__(
        self,
        event_type: EventType | str,
        session_id: str,
        payload: Optional[Dict[str, Any]] = None,
        step: Optional[str] = None,
        worker: Optional[str] = None,
        timestamp: Optional[float] = None,
    ):
        self.event_type = event_type.value if hasattr(event_type, "value") else str(event_type)
        self.session_id = session_id
        self.payload = payload or {}
        self.step = step
        self.worker = worker
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "session_id": self.session_id,
            "step": self.step,
            "worker": self.worker,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class EventBus:
    """
    Bus d'événements synchrone et asynchrone permettant à l'UI, aux logs et
    au système de télémétrie de s'abonner aux transitions du pipeline en direct.
    """

    def __init__(self):
        self._subscribers: List[Callable[[AgentEvent], None]] = []

    def subscribe(self, callback: Callable[[AgentEvent], None]) -> Callable[[], None]:
        """Abonne un listener. Retourne une fonction pour se désabonner."""
        self._subscribers.append(callback)

        def unsubscribe():
            if callback in self._subscribers:
                self._subscribers.remove(callback)

        return unsubscribe

    def emit(
        self,
        event_type: EventType | str,
        session_id: str,
        payload: Optional[Dict[str, Any]] = None,
        step: Optional[str] = None,
        worker: Optional[str] = None,
    ) -> AgentEvent:
        """Publie un événement à tous les observateurs enregistrés."""
        event = AgentEvent(
            event_type=event_type,
            session_id=session_id,
            payload=payload,
            step=step,
            worker=worker,
        )
        for callback in list(self._subscribers):
            try:
                callback(event)
            except Exception as e:
                # Évite qu'une erreur de logging ou d'UI n'interrompe le pipeline principal
                pass
        return event
