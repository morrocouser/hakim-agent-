#!/usr/bin/env python3
"""
HakimAgent - Benchmark Comparatif des Modes OmniRoute (Port 20128)
Évalue et compare les 3 modes intelligents d'OmniRoute :
  1. omniroute/auto/best-fast
  2. omniroute/auto/best-coding
  3. omniroute/auto/best-reasoning
Sur 3 épreuves standardisées :
  - Épreuve A : Décomposition & Planification (Supervisor)
  - Épreuve B : Génération & Exécution de Code Python (Executor + Sandbox)
  - Épreuve C : Résolution Complète End-to-End orchestrée (Pipeline Hub & Spokes)
"""

import os
import sys
import io
import time
import json
import statistics
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

site_packages = BACKEND / ".venv" / "Lib" / "site-packages"
if site_packages.exists() and str(site_packages) not in sys.path:
    sys.path.insert(0, str(site_packages))

from axiom.claude.client import LocalAPIClient
from hakim_agent.supervisor import SupervisorAgent
from hakim_agent.workers.executor import CodeExecutorWorker
from hakim_agent.workers.reviewer import ReviewerWorker
from hakim_agent.orchestrator import HakimOrchestrator
from hakim_agent.state import AgentStatus

G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
M = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RST = "\033[0m"


@dataclass
class ModeBenchmarkScore:
    mode_name: str
    label: str
    planning_time_s: float = 0.0
    planning_steps_count: int = 0
    planning_success: bool = False
    
    code_gen_time_s: float = 0.0
    code_exec_success: bool = False
    code_output: str = ""
    
    e2e_time_s: float = 0.0
    e2e_success: bool = False
    e2e_math_match: bool = False
    
    total_time_s: float = 0.0
    score_100: float = 0.0
    errors: List[str] = field(default_factory=list)


async def run_benchmark_for_mode(client: LocalAPIClient, mode_id: str, label: str) -> ModeBenchmarkScore:
    score = ModeBenchmarkScore(mode_name=mode_id, label=label)
    print(f"\n{BOLD}{M}======================================================================{RST}")
    print(f"{BOLD}{M}  ÉVALUATION DU MODE OMNIROUTE : {mode_id.upper()}{RST}")
    print(f"  {DIM}{label}{RST}")
    print(f"{BOLD}{M}======================================================================{RST}")

    t_start_all = time.perf_counter()

    # Configuration des variables d'environnement pour ce mode
    os.environ["HAKIM_LLM_MODEL"] = mode_id
    os.environ["HAKIM_MODEL_CODE"] = mode_id

    # -------------------------------------------------------------
    # 1. ÉPREUVE A : DÉCOMPOSITION & PLANIFICATION SUPERVISEUR
    # -------------------------------------------------------------
    print(f"\n  {BOLD}{C}▶ Test A : Planification & Décomposition Structurée{RST}")
    supervisor = SupervisorAgent(llm_client=client)
    prompt_plan = "Créer un script de scraping pour extraire les cours des actions, calculer la moyenne mobile et générer un rapport PDF"
    
    t0 = time.perf_counter()
    try:
        plan = await supervisor.create_plan_async(prompt_plan)
        score.planning_time_s = time.perf_counter() - t0
        score.planning_steps_count = len(plan)
        if len(plan) >= 2:
            score.planning_success = True
            print(f"    {G}✔ [SUCCÈS]{RST} Plan généré en {score.planning_time_s:.2f}s ({len(plan)} étapes claires)")
            for i, step in enumerate(plan):
                print(f"      {DIM}{i+1}. {step}{RST}")
        else:
            print(f"    {R}✖ [ÉCHEC]{RST} Moins de 2 étapes générées ({len(plan)})")
            score.errors.append("Plan trop court")
    except Exception as e:
        score.planning_time_s = time.perf_counter() - t0
        print(f"    {R}✖ [ERREUR]{RST} Exception planification: {e}")
        score.errors.append(f"Plan error: {e}")

    # -------------------------------------------------------------
    # 2. ÉPREUVE B : GÉNÉRATION & EXÉCUTION SANDBOX PYTHON
    # -------------------------------------------------------------
    print(f"\n  {BOLD}{C}▶ Test B : Génération & Exécution de Code Algorithmique (Factorielle & Somme){RST}")
    executor = CodeExecutorWorker(timeout_seconds=15, llm_client=client)
    instruction = "Écrire et exécuter un script Python qui calcule la factorielle de 6 et affiche 'RESULTAT=' suivi de la valeur"

    t0 = time.perf_counter()
    try:
        res = await executor.execute(instruction, {})
        score.code_gen_time_s = time.perf_counter() - t0
        stdout = res.get("stdout", "").strip()
        score.code_output = stdout
        # Factorielle 6 = 720
        if res.get("success") and "720" in stdout:
            score.code_exec_success = True
            print(f"    {G}✔ [SUCCÈS]{RST} Code exécuté et vérifié en {score.code_gen_time_s:.2f}s | Sortie: {stdout}")
        elif res.get("success"):
            score.code_exec_success = False
            print(f"    {Y}⚠ [PARTIEL]{RST} Code exécuté en {score.code_gen_time_s:.2f}s mais résultat attendu (720) non trouvé : {stdout}")
            score.errors.append(f"Result mismatch: {stdout}")
        else:
            print(f"    {R}✖ [ÉCHEC]{RST} Échec exécution: {res.get('stderr') or res.get('output')}")
            score.errors.append(f"Exec fail: {res.get('stderr')}")
    except Exception as e:
        score.code_gen_time_s = time.perf_counter() - t0
        print(f"    {R}✖ [ERREUR]{RST} Exception génération code: {e}")
        score.errors.append(f"Code gen error: {e}")

    # -------------------------------------------------------------
    # 3. ÉPREUVE C : PIPELINE END-TO-END COMPLET AVEC REVIEWER
    # -------------------------------------------------------------
    print(f"\n  {BOLD}{C}▶ Test C : Pipeline Complet Hub & Spokes (Plan -> Exec -> Review){RST}")
    orchestrator = HakimOrchestrator(
        supervisor=supervisor,
        max_fix_retries=2,
    )
    prompt_e2e = (
        "1. Calculer la somme des carrés des nombres de 1 à 4 (1^2 + 2^2 + 3^2 + 4^2) en Python et afficher le total\n"
        "2. Valider le résultat mathématique obtenu"
    )

    t0 = time.perf_counter()
    try:
        session_id = f"bench_omni_{mode_id.split('/')[-1]}_{int(time.time())}"
        state = await orchestrator.run(prompt=prompt_e2e, session_id=session_id)
        score.e2e_time_s = time.perf_counter() - t0
        
        # 1 + 4 + 9 + 16 = 30
        expected_math = "30"
        found_math = any(expected_math in str(v) for v in state.get("context", {}).values())

        if state.get("status") == AgentStatus.COMPLETED.value and found_math:
            score.e2e_success = True
            score.e2e_math_match = True
            print(f"    {G}✔ [SUCCÈS]{RST} Pipeline complet achevé avec validation mathématique en {score.e2e_time_s:.2f}s (Total: 30)")
        elif state.get("status") == AgentStatus.COMPLETED.value:
            score.e2e_success = True
            print(f"    {Y}⚠ [VALIDÉ SANS ASSERTION]{RST} Statut completed en {score.e2e_time_s:.2f}s mais 30 non trouvé expressément.")
        else:
            print(f"    {R}✖ [ÉCHEC]{RST} Statut pipeline: {state.get('status')}")
            score.errors.append(f"E2E fail status: {state.get('status')}")
    except Exception as e:
        score.e2e_time_s = time.perf_counter() - t0
        print(f"    {R}✖ [ERREUR]{RST} Exception E2E: {e}")
        score.errors.append(f"E2E error: {e}")

    score.total_time_s = time.perf_counter() - t_start_all

    # Calcul du score sur 100
    points = 0.0
    if score.planning_success: points += 30.0
    if score.code_exec_success: points += 35.0
    if score.e2e_success: points += 20.0
    if score.e2e_math_match: points += 15.0
    score.score_100 = round(points, 1)

    print(f"\n  🎯 {BOLD}Score pour {mode_id} : {score.score_100}/100{RST} (Temps total: {score.total_time_s:.2f}s)")
    return score


async def main():
    print(f"\n{BOLD}{C}========================================================================{RST}")
    print(f"{BOLD}{C}  🏆 BENCHMARK COMPARATIF OMNIROUTE MODES - HAKIMAGENT ENGINE{RST}")
    print(f"{BOLD}{C}========================================================================{RST}")
    print(f"  Passerelle OmniRoute : http://127.0.0.1:20128/v1")
    print(f"  Environnement        : Python 3.11 sur Windows x64\n")

    client = LocalAPIClient()
    if not client.is_configured():
        print(f"{R}Erreur: Le client OmniRoute n'est pas joignable sur http://127.0.0.1:20128/v1{RST}")
        return

    modes = [
        ("omniroute/auto/best-fast", "Modèle Ultra-Rapide / Latence Minimale"),
        ("omniroute/auto/best-coding", "Modèle Expert Code & Synthèse"),
        ("omniroute/auto/best-reasoning", "Modèle Raisonnement Profond & Chaîne de Pensée"),
    ]

    all_scores: List[ModeBenchmarkScore] = []
    for mode_id, label in modes:
        score = await run_benchmark_for_mode(client, mode_id, label)
        all_scores.append(score)

    # =========================================================================
    # TABLEAU COMPARATIF FINAL
    # =========================================================================
    print(f"\n{BOLD}{C}========================================================================{RST}")
    print(f"{BOLD}{C}  📊 TABLEAU COMPARATIF FINAL DES PERFORMANCES OMNIROUTE{RST}")
    print(f"{BOLD}{C}========================================================================{RST}\n")

    print(f"  {'Mode OmniRoute':<30} | {'Planif (s)':<10} | {'Code (s)':<10} | {'E2E (s)':<10} | {'Total (s)':<10} | {'Score /100':<10}")
    print(f"  {'-' * 30}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 10}")

    for s in all_scores:
        col = G if s.score_100 >= 90 else (Y if s.score_100 >= 70 else R)
        print(f"  {s.mode_name:<30} | {s.planning_time_s:>8.2f}s  | {s.code_gen_time_s:>8.2f}s  | {s.e2e_time_s:>8.2f}s  | {s.total_time_s:>8.2f}s  | {col}{s.score_100:>8.1f}/100{RST}")

    print(f"  {'-' * 30}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 10}")

    # Recommandation automatique
    fastest = min(all_scores, key=lambda x: x.total_time_s)
    best_scored = max(all_scores, key=lambda x: x.score_100)

    print(f"\n  ⚡ {BOLD}Le Plus Rapide{RST}       : {C}{fastest.mode_name}{RST} ({fastest.total_time_s:.2f}s total)")
    print(f"  🎯 {BOLD}Le Plus Performant{RST}   : {G}{best_scored.mode_name}{RST} ({best_scored.score_100}/100)")
    print()

    # Sauvegarde JSON
    export_file = ROOT / "omniroute_benchmark_comparison.json"
    data = [
        {
            "mode": s.mode_name,
            "label": s.label,
            "score_100": s.score_100,
            "total_time_s": round(s.total_time_s, 2),
            "planning_time_s": round(s.planning_time_s, 2),
            "code_gen_time_s": round(s.code_gen_time_s, 2),
            "e2e_time_s": round(s.e2e_time_s, 2),
            "planning_success": s.planning_success,
            "code_exec_success": s.code_exec_success,
            "e2e_success": s.e2e_success,
            "errors": s.errors,
        }
        for s in all_scores
    ]
    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  💾 Données de benchmark sauvegardées dans : {export_file}\n")


if __name__ == "__main__":
    asyncio.run(main())
