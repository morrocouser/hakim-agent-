"""
HakimAgent - Boucle d'Orchestration (Étape 4)

Coordonne le Superviseur, les Spécialistes, la boucle de Review/Auto-fix,
le Bus d'événements et la persistance locale continue (SQLite/JSON).
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

from hakim_agent.state import (
    AgentState,
    AgentStatus,
    EventBus,
    EventType,
    create_initial_state,
)
from hakim_agent.storage import SessionStorage
from hakim_agent.supervisor import SupervisorAgent
from hakim_agent.workers.base import BaseWorker
from hakim_agent.workers.executor import CodeExecutorWorker
from hakim_agent.workers.researcher import ResearcherWorker
from hakim_agent.workers.reviewer import ReviewerWorker


class HakimOrchestrator:
    """
    Moteur d'orchestration Hub & Spokes pour HakimAgent.
    Gère la décomposition, le routage, la validation et la reprise sur incident.
    """

    def __init__(
        self,
        supervisor: Optional[SupervisorAgent] = None,
        storage: Optional[SessionStorage] = None,
        event_bus: Optional[EventBus] = None,
        max_fix_retries: int = 3,
    ):
        self.supervisor = supervisor or SupervisorAgent()
        self.storage = storage or SessionStorage()
        self.event_bus = event_bus or EventBus()
        self.max_fix_retries = max_fix_retries

    async def run(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        resume: bool = True,
    ) -> AgentState:
        """
        Exécute le pipeline complet pour un prompt donné.
        Si resume=True et que la session existe, reprend là où elle s'est arrêtée.
        """
        # 1. Initialisation ou reprise d'état
        existing_state = self.storage.load_session(session_id) if session_id else None
        
        if existing_state and resume and existing_state.get("status") != AgentStatus.COMPLETED.value:
            state = existing_state
            state["status"] = AgentStatus.RUNNING.value
        else:
            state = create_initial_state(prompt=prompt, session_id=session_id)
            state["status"] = AgentStatus.RUNNING.value

        sid = state["session_id"]
        self.event_bus.emit(EventType.PIPELINE_START, session_id=sid, payload={"prompt": prompt, "resume": bool(existing_state)})

        # 2. Planification si non existante
        if not state.get("plan"):
            state["plan"] = await self.supervisor.create_plan_async(state["user_prompt"])
            self.event_bus.emit(EventType.PLAN_CREATED, session_id=sid, payload={"plan": state["plan"]})
            self.storage.save_checkpoint(state)

        plan = state["plan"]
        current_step_idx = state.get("current_step", 0)

        # 3. Boucle d'exécution des étapes
        try:
            while current_step_idx < len(plan):
                step = plan[current_step_idx]
                self.event_bus.emit(EventType.STEP_START, session_id=sid, step=step, payload={"step_index": current_step_idx})

                # A. Routage par le Superviseur
                target_agent: BaseWorker = self.supervisor.route_step(step)
                self.event_bus.emit(EventType.STEP_ROUTED, session_id=sid, step=step, worker=target_agent.name)

                # B. Exécution par le spécialiste
                self.event_bus.emit(EventType.WORKER_START, session_id=sid, step=step, worker=target_agent.name)
                result = await target_agent.execute(step, state["context"], state)
                self.event_bus.emit(
                    EventType.WORKER_OUTPUT,
                    session_id=sid,
                    step=step,
                    worker=target_agent.name,
                    payload={"result": result},
                )
                state["context"][step] = result

                # C. Contrôle de validation (Reviewer) si modification critique
                if target_agent.requires_review:
                    self.event_bus.emit(EventType.REVIEW_START, session_id=sid, step=step, worker=self.supervisor.reviewer.name)
                    is_valid, feedback = self.supervisor.reviewer.check(result)
                    self.event_bus.emit(
                        EventType.REVIEW_RESULT,
                        session_id=sid,
                        step=step,
                        payload={"is_valid": is_valid, "feedback": feedback},
                    )

                    # Boucle de correction si nécessaire (bornée à max_fix_retries)
                    retries = 0
                    while not is_valid and retries < self.max_fix_retries:
                        retries += 1
                        self.event_bus.emit(
                            EventType.CORRECTION_START,
                            session_id=sid,
                            step=step,
                            worker=target_agent.name,
                            payload={"retry": retries, "feedback": feedback},
                        )
                        result = await target_agent.fix(step, result, feedback, state["context"])
                        state["context"][step] = result
                        
                        # Re-check après fix
                        is_valid, feedback = self.supervisor.reviewer.check(result)
                        self.event_bus.emit(
                            EventType.CORRECTION_RESULT,
                            session_id=sid,
                            step=step,
                            payload={"retry": retries, "is_valid": is_valid, "feedback": feedback},
                        )

                # D. Mise à jour de l'historique et sauvegarde
                state["history"].append({
                    "step_index": current_step_idx,
                    "step": step,
                    "worker": target_agent.name,
                    "timestamp": time.time(),
                })
                current_step_idx += 1
                state["current_step"] = current_step_idx

                # Sauvegarde du checkpoint en SQLite après chaque tour
                self.storage.save_checkpoint(state, step_name=step, step_result=result)
                self.event_bus.emit(EventType.CHECKPOINT_SAVED, session_id=sid, step=step, payload={"current_step": current_step_idx})
                self.event_bus.emit(EventType.STEP_FINISH, session_id=sid, step=step)

            # Fin du pipeline avec succès
            state["status"] = AgentStatus.COMPLETED.value
            self.storage.save_checkpoint(state)
            self.event_bus.emit(EventType.PIPELINE_FINISH, session_id=sid, payload={"status": state["status"]})

        except Exception as e:
            state["status"] = AgentStatus.FAILED.value
            state["context"]["_error"] = str(e)
            self.storage.save_checkpoint(state)
            self.event_bus.emit(EventType.ERROR, session_id=sid, payload={"error": str(e)})
            raise

        return state


def run_hakim_pipeline(prompt: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fonction d'orchestration directe conforme à la signature demandée :
    run_hakim_pipeline(prompt: str) -> state["context"]
    """
    orchestrator = HakimOrchestrator()
    
    # Exécution synchrone protégée pour CLI/scripts
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Déjà dans une boucle active
        import nest_asyncio
        nest_asyncio.apply()
        state = loop.run_until_complete(orchestrator.run(prompt, session_id=session_id))
    else:
        state = asyncio.run(orchestrator.run(prompt, session_id=session_id))

    return state["context"]
