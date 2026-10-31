#!/usr/bin/env python3
"""
Test de HakimAgent utilisant les modes d'OmniRoute (Port 20128) :
- omniroute/auto/best-fast
- omniroute/auto/best-coding
- omniroute/auto/best-reasoning
"""

import os
import sys
import time
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))
site_packages = BACKEND_DIR / ".venv" / "Lib" / "site-packages"
if site_packages.exists() and str(site_packages) not in sys.path:
    sys.path.insert(0, str(site_packages))

from axiom.claude.client import LocalAPIClient
from hakim_agent.supervisor import SupervisorAgent
from hakim_agent.workers.executor import CodeExecutorWorker
from hakim_agent.workers.reviewer import ReviewerWorker
from hakim_agent.orchestrator import HakimOrchestrator
from hakim_agent.state import EventBus, EventType, AgentStatus


def banner(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


async def main():
    banner("1. VÉRIFICATION DU CLIENT OMNIROUTE (PORT 20128)")
    client = LocalAPIClient()
    print(f"  * URL de base du routeur : {client.base_url}")
    print(f"  * Client configuré       : {client.is_configured()}")

    # Modes à tester
    modes = [
        ("omniroute/auto/best-fast", "Mode Véloce / Faible Latence", "En 1 phrase, qu'est-ce qu'une API REST ?"),
        ("omniroute/auto/best-coding", "Mode Spécialisé Programmation", "Écris un script Python calculant la somme des carrés de 1 à 5."),
        ("omniroute/auto/best-reasoning", "Mode Réflexion & Logique", "Un train part à 10h à 100km/h pour faire 250km. À quelle heure arrive-t-il ?"),
    ]

    for model_id, label, query in modes:
        banner(f"Test du Mode : {model_id} ({label})")
        t0 = time.time()
        try:
            resp = await client.chat(
                model=model_id,
                system="Tu es un assistant IA précis et concis.",
                messages=[{"role": "user", "content": query}],
                max_tokens=400,
            )
            elapsed = time.time() - t0
            print(f"  ✅ Réponse reçue en {elapsed:.2f}s :")
            clean_resp = resp.strip()
            print(f"  {clean_resp[:350]}...")
        except Exception as e:
            print(f"  ❌ Erreur sur {model_id} : {e}")

    banner("2. TEST END-TO-END : HAKIMAGENT AVEC OMNIROUTE (BEST-CODING)")
    bus = EventBus()
    events = []

    def on_ev(e):
        events.append(str(e.event_type))

    bus.subscribe(on_ev)

    # Superviseur et workers configurés pour utiliser OmniRoute
    os.environ["HAKIM_LLM_MODEL"] = "omniroute/auto/best-coding"
    os.environ["HAKIM_MODEL_CODE"] = "omniroute/auto/best-coding"

    supervisor = SupervisorAgent(llm_client=client)
    orchestrator = HakimOrchestrator(
        supervisor=supervisor,
        event_bus=bus,
        max_fix_retries=2,
    )

    prompt = (
        "1. Générer et exécuter le script Python calculant la suite de Fibonacci jusqu'à 8 termes\n"
        "2. Vérifier l'absence d'erreurs et valider l'exécution"
    )
    print(f"  * Requête soumise à l'Orchestrateur :\n{prompt}")

    t0 = time.time()
    state = await orchestrator.run(prompt=prompt, session_id="omniroute_test_session")
    elapsed = time.time() - t0

    print(f"\n  * Statut final : {state['status']}")
    print(f"  * Durée globale : {elapsed:.2f}s")
    print(f"  * Plan suivi ({len(state['plan'])} étapes) :")
    for i, st in enumerate(state["plan"]):
        print(f"    {i+1}. {st}")

    print(f"  * Historique d'exécution :")
    for h in state["history"]:
        print(f"    - Étape {h['step_index']+1} par [{h['worker']}]")

    print(f"  * Contexte généré : {list(state['context'].keys())}")
    for k, v in state["context"].items():
        if isinstance(v, dict) and "output" in v:
            print(f"    -> Output : {v['output'].strip()[:150]}")

    print(f"  * Événements EventBus : {len(events)} capturés")
    assert state["status"] == AgentStatus.COMPLETED.value
    print("\n  ✅ HakimAgent fonctionne avec succès sur les modes OmniRoute !")


if __name__ == "__main__":
    asyncio.run(main())
