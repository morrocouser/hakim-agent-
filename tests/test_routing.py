"""
HakimAgent - Tests Unitaires de Routage et de Délégation Multi-Agents (Étape 3)
Valide les 3 cas d'usage sans interface graphique :
- Cas 1 (Agent unique) : Requête UI/UX -> délégation exclusive à @ux_designer
- Cas 2 (Développement) : Demande de composant de code -> délégation à @frontend_dev
- Cas 3 (Pipeline Multi-Agents) : "Conçois un bouton minimaliste sombre, code-le et vérifie le code"
  -> transmission séquentielle de contexte @ux_designer -> @frontend_dev -> @qa_reviewer
"""

import sys
import pytest
import asyncio
from pathlib import Path

# Force l'encodage UTF-8 pour Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from hakim_agent.supervisor import SupervisorAgent
from hakim_agent.orchestrator import HakimOrchestrator
from hakim_agent.state import AgentStatus, EventBus
from hakim_agent.workers.ux_designer import UXDesignerWorker
from hakim_agent.workers.frontend_dev import FrontendDevWorker
from hakim_agent.workers.reviewer import ReviewerWorker


@pytest.fixture
def supervisor():
    """Superviseur instancié en mode heuristique rapide et déterministe (sans appel réseau)."""
    return SupervisorAgent(llm_client=False)


@pytest.fixture
def orchestrator(supervisor):
    """Orchestrateur HakimAgent avec EventBus."""
    bus = EventBus()
    return HakimOrchestrator(supervisor=supervisor, event_bus=bus, max_fix_retries=2)


@pytest.mark.asyncio
async def test_case_1_single_agent_ux_designer(supervisor, orchestrator):
    """
    Cas 1 (Agent unique) :
    Une demande purement UI/UX doit être déléguée uniquement à @ux_designer.
    """
    prompt = "Conçois la maquette UI/UX et les spécifications d'ergonomie d'une interface épurée"

    # 1. Vérification du plan
    plan = supervisor.create_plan(prompt)
    assert len(plan) == 1, f"Attendu 1 étape UI/UX, obtenu {len(plan)}: {plan}"
    assert any(k in plan[0].lower() for k in ["ui/ux", "spécifications", "concevoir"])

    # 2. Vérification du routage direct
    target_worker = supervisor.route_step(plan[0])
    assert isinstance(target_worker, UXDesignerWorker)
    assert target_worker.name == "@ux_designer"

    # 3. Exécution via l'orchestrateur
    state = await orchestrator.run(prompt=prompt, session_id="test_routing_case_1")
    assert state["status"] == AgentStatus.COMPLETED.value
    assert len(state["history"]) == 1
    assert state["history"][0]["worker"] == "@ux_designer"

    # 4. Vérification du livrable produit
    step_key = state["plan"][0]
    result = state["context"][step_key]
    assert result.get("success") is True
    assert "design_tokens" in result
    assert result["agent"] == "@ux_designer"
    print("\n  ✅ Cas 1 (Agent unique @ux_designer) validé avec succès !")


@pytest.mark.asyncio
async def test_case_2_single_agent_frontend_dev(supervisor, orchestrator):
    """
    Cas 2 (Développement) :
    Une demande de composant de code doit être déléguée à @frontend_dev.
    """
    prompt = "Code un composant de bouton interactif avec Tailwind CSS"

    # 1. Vérification du plan
    plan = supervisor.create_plan(prompt)
    assert len(plan) >= 1
    assert any(k in plan[0].lower() for k in ["composant", "code", "développer"])

    # 2. Vérification du routage direct
    target_worker = supervisor.route_step(plan[0])
    assert isinstance(target_worker, FrontendDevWorker)
    assert target_worker.name == "@frontend_dev"

    # 3. Exécution via l'orchestrateur
    state = await orchestrator.run(prompt=prompt, session_id="test_routing_case_2")
    assert state["status"] == AgentStatus.COMPLETED.value
    
    # 4. Vérification du code généré
    step_key = state["plan"][0]
    result = state["context"][step_key]
    assert result.get("success") is True
    assert "code" in result
    assert "export const" in result["code"]
    assert result["agent"] == "@frontend_dev"
    print("\n  ✅ Cas 2 (Développement @frontend_dev) validé avec succès !")


@pytest.mark.asyncio
async def test_case_3_multi_agent_pipeline_sequential_context(supervisor, orchestrator):
    """
    Cas 3 (Pipeline Multi-Agents) :
    Demande complète : 'Conçois un bouton minimaliste sombre, code-le et vérifie le code'
    Vérifie le passage séquentiel du contexte : @ux_designer -> @frontend_dev -> @qa_reviewer.
    """
    prompt = "Conçois un bouton minimaliste sombre, code-le et vérifie le code"

    # 1. Vérification du découpage en 3 étapes distinctes
    plan = supervisor.create_plan(prompt)
    assert len(plan) == 3, f"Le plan doit comporter 3 étapes ordonnées, reçu : {plan}"

    # 2. Vérification du routage ordonné des étapes
    worker_1 = supervisor.route_step(plan[0])
    worker_2 = supervisor.route_step(plan[1])
    worker_3 = supervisor.route_step(plan[2])

    assert isinstance(worker_1, UXDesignerWorker), f"Étape 1 doit être @ux_designer, reçu {worker_1}"
    assert isinstance(worker_2, FrontendDevWorker), f"Étape 2 doit être @frontend_dev, reçu {worker_2}"
    assert isinstance(worker_3, ReviewerWorker), f"Étape 3 doit être @qa_reviewer, reçu {worker_3}"

    assert worker_1.name == "@ux_designer"
    assert worker_2.name == "@frontend_dev"
    assert worker_3.name == "@qa_reviewer"

    # 3. Exécution du pipeline complet
    state = await orchestrator.run(prompt=prompt, session_id="test_routing_case_3")
    assert state["status"] == AgentStatus.COMPLETED.value
    assert state["current_step"] == 3

    # 4. Vérification de la séquence dans l'historique
    workers_invoked = [h["worker"] for h in state["history"]]
    assert workers_invoked == ["@ux_designer", "@frontend_dev", "@qa_reviewer"], (
        f"L'ordre d'exécution séquentiel est incorrect : {workers_invoked}"
    )

    # 5. Vérification de la transmission du contexte
    ux_result = state["context"][state["plan"][0]]
    frontend_result = state["context"][state["plan"][1]]
    qa_result = state["context"][state["plan"][2]]

    # A. @ux_designer a émis des tokens sombres minimalistes
    assert ux_result["success"] is True
    assert ux_result["design_tokens"]["theme"] == "dark"
    assert ux_result["design_tokens"]["style"] == "minimalist"

    # B. @frontend_dev a hérité des spécifications UX pour coder le composant
    assert frontend_result["success"] is True
    assert frontend_result["inherited_ux_spec"] is True, "Le frontend_dev n'a pas reçu le contexte du @ux_designer !"
    assert "bg-zinc-900" in frontend_result["code"]  # Vérifie l'application du token sombre

    # C. @qa_reviewer a validé l'ensemble du livrable
    assert qa_result["success"] is True
    assert qa_result["is_valid"] is True
    assert qa_result["agent"] == "@qa_reviewer"

    print("\n  ✅ Cas 3 (Pipeline Multi-Agents Séquentiel) validé avec succès !")
    print(f"     Séquence : {' -> '.join(workers_invoked)}")
    print("     Transmission de contexte : @ux_designer -> @frontend_dev (hérité) -> @qa_reviewer (validé)")


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 EXÉCUTION DES TESTS UNITAIRES DE ROUTAGE ET DÉLÉGATION")
    print("=" * 70)
    sup = SupervisorAgent(llm_client=False)
    orch = HakimOrchestrator(supervisor=sup, event_bus=EventBus())
    asyncio.run(test_case_1_single_agent_ux_designer(sup, orch))
    asyncio.run(test_case_2_single_agent_frontend_dev(sup, orch))
    asyncio.run(test_case_3_multi_agent_pipeline_sequential_context(sup, orch))
    print("=" * 70)
    print("🎉 TOUS LES TESTS DE ROUTAGE ET DÉLÉGATION ONT RÉUSSI !")
    print("=" * 70)
