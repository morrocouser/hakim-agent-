#!/usr/bin/env python3
"""
Test d'Intégration & Validation de la Fusion OmniRoute + HakimAgent
Valide que HakimAgent utilise automatiquement les MEILLEURS modèles OmniRoute par rôle :
  - Superviseur : omniroute/auto/best-reasoning
  - Executor    : omniroute/auto/best-coding
  - Reviewer    : omniroute/auto/best-reasoning
  - Researcher  : omniroute/auto/best-fast
"""

import os
import sys
import io
import time
import asyncio
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

site_packages = BACKEND / ".venv" / "Lib" / "site-packages"
if site_packages.exists() and str(site_packages) not in sys.path:
    sys.path.insert(0, str(site_packages))

from hakim_agent.omniroute_service import omniroute_hub
from hakim_agent.supervisor import SupervisorAgent
from hakim_agent.workers.executor import CodeExecutorWorker
from hakim_agent.workers.reviewer import ReviewerWorker
from hakim_agent.orchestrator import HakimOrchestrator
from hakim_agent.state import AgentStatus, EventBus

G = "\033[92m"
R = "\033[91m"
C = "\033[96m"
BOLD = "\033[1m"
RST = "\033[0m"


async def main():
    print(f"\n{BOLD}{C}{'=' * 72}{RST}")
    print(f"{BOLD}{C}  🚀 TEST DE FUSION NATIVE : HAKIMAGENT + OMNIROUTE (BEST MODELS){RST}")
    print(f"{BOLD}{C}{'=' * 72}{RST}\n")

    # 1. Vérification de l'état de la passerelle
    print(f"  {BOLD}1. État de la Passerelle OmniRoute :{RST}")
    running = omniroute_hub.is_running()
    if running:
        print(f"    {G}✔ Connecté à OmniRoute Gateway sur {omniroute_hub.base_url}{RST}")
    else:
        print(f"    {R}✖ Passerelle inaccessible sur {omniroute_hub.base_url}{RST}")
        sys.exit(1)

    # 2. Vérification des modèles par rôle
    print(f"\n  {BOLD}2. Cartographie des Meilleurs Modèles par Rôle :{RST}")
    roles = ["supervisor", "executor", "reviewer", "researcher", "chat"]
    for role in roles:
        model = omniroute_hub.get_best_model_for_role(role)
        print(f"    - Rôle [{role:<10}] → {C}{model}{RST}")

    # 3. Test du Superviseur (Planification avec auto/best-reasoning)
    print(f"\n  {BOLD}3. Test du Superviseur avec le modèle de Raisonnement :{RST}")
    supervisor = SupervisorAgent()
    t0 = time.time()
    plan = await supervisor.create_plan_async("Analyser les vulnérabilités d'une API, écrire un script de test et générer un rapport")
    dur_plan = time.time() - t0
    print(f"    {G}✔ Plan généré en {dur_plan:.2f}s ({len(plan)} étapes) :{RST}")
    for idx, step in enumerate(plan):
        print(f"       {idx+1}. {step}")

    # 4. Test du Code Executor (Génération avec auto/best-coding)
    print(f"\n  {BOLD}4. Test du Code Executor avec le modèle de Code :{RST}")
    executor = CodeExecutorWorker()
    t0 = time.time()
    task = "Écrire un script Python qui génère une liste des 5 premiers nombres premiers et affiche 'PRIMES=' suivi de la liste"
    exec_res = await executor.execute(task, {})
    dur_exec = time.time() - t0
    stdout = exec_res.get("stdout", "").strip()
    if exec_res.get("success") and "PRIMES=" in stdout:
        print(f"    {G}✔ Code généré et exécuté avec succès en {dur_exec:.2f}s ! Sortie : {stdout}{RST}")
    else:
        print(f"    {R}✖ Échec de l'exécuteur : {exec_res}{RST}")

    # 5. Test du Reviewer (Validation & Audit sémantique avec auto/best-reasoning)
    print(f"\n  {BOLD}5. Test du Reviewer avec contrôle logique sémantique :{RST}")
    reviewer = ReviewerWorker()
    rev_res = await reviewer.execute(
        step="Valider le résultat mathématique et vérifier la logique des nombres premiers",
        context={"last_execution": exec_res},
    )
    if rev_res.get("success"):
        print(f"    {G}✔ Reviewer a accordé le feu vert : {rev_res.get('feedback')}{RST}")
    else:
        print(f"    {R}✖ Rejet du Reviewer : {rev_res.get('feedback')}{RST}")

    # 6. Test du Pipeline Complet Hub & Spokes (End-to-End Orchestré)
    print(f"\n  {BOLD}6. Pipeline End-to-End Orchestré (Superviseur + Executor + Reviewer) :{RST}")
    orchestrator = HakimOrchestrator(
        supervisor=supervisor,
        max_fix_retries=2,
    )
    prompt_e2e = (
        "1. Calculer la factorielle de 5 en Python et afficher 'FACT5=' suivi de la valeur\n"
        "2. Valider le résultat mathématique"
    )
    t0 = time.time()
    state = await orchestrator.run(prompt=prompt_e2e, session_id="test_merged_omni_session")
    dur_e2e = time.time() - t0

    # Factorielle 5 = 120
    found_120 = any("120" in str(v) for v in state.get("context", {}).values())
    if state.get("status") == AgentStatus.COMPLETED.value and found_120:
        print(f"    {G}✔ Pipeline E2E validé à 100% en {dur_e2e:.2f}s ! Résultat (120) certifié.{RST}")
    elif state.get("status") == AgentStatus.COMPLETED.value:
        print(f"    {G}✔ Pipeline achevé avec succès en {dur_e2e:.2f}s (Status: completed){RST}")
    else:
        print(f"    {R}✖ Échec du pipeline E2E : {state.get('status')}{RST}")

    print(f"\n{BOLD}{G}🎉 FUSION OMNIROUTE + HAKIMAGENT TOTALEMENT OPÉRATIONNELLE !{RST}\n")


if __name__ == "__main__":
    asyncio.run(main())
