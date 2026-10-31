"""
Tests unitaires et d'intégration pour le pipeline HakimAgent (Hub & Spokes).
Vérifie les 5 étapes d'implémentation :
- Étape 1 : Le State partagé et le bus d'événements
- Étape 2 : L'Agent Superviseur (Routeur)
- Étape 3 : Les Agents Spécialisés (Executor, Researcher, Reviewer)
- Étape 4 : Le Contrôle d'exécution et boucle d'auto-correction
- Étape 5 : Mémoire et Sauvegarde Locale (SQLite + Reprise de session)
"""

import os
import sys
import tempfile
import pytest
import asyncio
from pathlib import Path

# Assure que le dossier 'backend' est dans sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from hakim_agent.state import (
    create_initial_state,
    EventBus,
    EventType,
    AgentStatus,
)
from hakim_agent.storage import SessionStorage
from hakim_agent.supervisor import SupervisorAgent
from hakim_agent.workers.executor import CodeExecutorWorker
from hakim_agent.workers.researcher import ResearcherWorker
from hakim_agent.workers.reviewer import ReviewerWorker
from hakim_agent.orchestrator import HakimOrchestrator, run_hakim_pipeline


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_sessions.db")
    yield db_path
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


def test_step1_state_and_event_bus():
    """Vérifie l'initialisation de l'état partagé et l'émission d'événements."""
    state = create_initial_state("Créer un script de scraping")
    assert state["user_prompt"] == "Créer un script de scraping"
    assert state["current_step"] == 0
    assert state["status"] == AgentStatus.PENDING.value
    assert isinstance(state["context"], dict)

    bus = EventBus()
    events_received = []

    def on_event(ev):
        events_received.append(ev)

    unsubscribe = bus.subscribe(on_event)
    bus.emit(EventType.STEP_START, session_id=state["session_id"], step="Step 1")
    assert len(events_received) == 1
    assert events_received[0].step == "Step 1"

    unsubscribe()
    bus.emit(EventType.STEP_FINISH, session_id=state["session_id"], step="Step 1")
    assert len(events_received) == 1  # Pas d'événement supplémentaire reçu après désabonnement


def test_step2_supervisor_planning_and_routing():
    """Vérifie le découpage en plan et le routage précis du Superviseur."""
    supervisor = SupervisorAgent()

    # Planification automatique
    plan = supervisor.create_plan("Recherche les specs FastAPI et génère un code Python de test")
    assert len(plan) >= 2

    # Routage
    agent_research = supervisor.route_step("Rechercher la documentation officielle de LangGraph")
    assert isinstance(agent_research, ResearcherWorker)

    agent_code = supervisor.route_step("Exécuter le script python de calcul de métriques")
    assert isinstance(agent_code, CodeExecutorWorker)

    agent_review = supervisor.route_step("Vérifier et valider les erreurs de syntaxe")
    assert isinstance(agent_review, ReviewerWorker)


@pytest.mark.asyncio
async def test_step3_code_executor_and_reviewer():
    """Vérifie l'exécution réelle de code et la validation du Reviewer."""
    executor = CodeExecutorWorker(timeout_seconds=5)
    reviewer = ReviewerWorker()

    # 1. Code valide
    python_code = "print('HAKIM_AGENT_OK')"
    res = await executor.execute(python_code, {})
    assert res["success"] is True
    assert "HAKIM_AGENT_OK" in res["stdout"]

    is_valid, feedback = reviewer.check(res)
    assert is_valid is True
    assert "Validation réussie" in feedback

    # 2. Code avec erreur de syntaxe
    invalid_code = "def bad_func( print('missing paren')"
    res_err = await executor.execute(invalid_code, {})
    is_valid, feedback = reviewer.check(res_err)
    assert is_valid is False
    assert "Erreur de syntaxe" in feedback or "Échec" in feedback


@pytest.mark.asyncio
async def test_step4_and_step5_pipeline_with_persistence_and_resume(temp_db):
    """Vérifie le cycle complet d'orchestration, la sauvegarde SQLite et la reprise."""
    storage = SessionStorage(db_path=temp_db)
    bus = EventBus()
    orchestrator = HakimOrchestrator(storage=storage, event_bus=bus)

    prompt = "Écrire et exécuter un script python qui affiche 42"
    state = await orchestrator.run(prompt=prompt, session_id="test_sess_001")

    assert state["status"] == AgentStatus.COMPLETED.value
    assert state["current_step"] == len(state["plan"])

    # Vérification dans SQLite
    saved_state = storage.load_session("test_sess_001")
    assert saved_state is not None
    assert saved_state["status"] == AgentStatus.COMPLETED.value
    assert saved_state["current_step"] == len(state["plan"])

    # Test de reprise de session
    # Simulons une session interrompue à l'étape 1 sur 3
    interrupted_state = create_initial_state("Session interrompue", session_id="sess_interrupted")
    interrupted_state["plan"] = ["Étape 1 terminée", "print('RESUME_SUCCESS')", "Vérifier"]
    interrupted_state["current_step"] = 1  # L'étape 0 est déjà faite
    interrupted_state["context"]["Étape 1 terminée"] = {"done": True}
    storage.save_checkpoint(interrupted_state)

    # Relançons l'orchestrateur sur la session
    resumed_state = await orchestrator.run(
        prompt="Session interrompue",
        session_id="sess_interrupted",
        resume=True,
    )
    assert resumed_state["status"] == AgentStatus.COMPLETED.value
    assert resumed_state["current_step"] == 3
    # L'étape 1 n'a pas été réexécutée, son contexte initial est préservé
    assert resumed_state["context"]["Étape 1 terminée"] == {"done": True}
    assert "print('RESUME_SUCCESS')" in resumed_state["context"]


def test_convenience_run_hakim_pipeline(temp_db):
    """Vérifie l'exécution de la fonction wrapper demandée."""
    context = run_hakim_pipeline("print('Hello from pipeline wrapper')")
    assert isinstance(context, dict)
    # L'étape exécutée doit figurer dans le contexte retourné
    assert len(context) > 0
