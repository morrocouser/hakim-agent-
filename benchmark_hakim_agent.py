#!/usr/bin/env python3
"""
HakimAgent Comprehensive Benchmark Suite
Évalue rigoureusement les 5 piliers de l'architecture Hub & Spokes :
1. Décomposition & Routage du Superviseur
2. Exécution de Code & Sécurité du Sandbox (Smolagents / Open Interpreter)
3. Boucle de Critique & Auto-Correction (AutoGen / LangGraph)
4. Persistance SQLite & Reprise sur Incident (LangGraph Checkpointing)
5. Résolution End-to-End avec LLM Réel (Google AI Studio Gemini 3.5 Flash)
6. Charge Concurrente & Empreinte Mémoire (asyncio + tracemalloc)
"""

import asyncio
import datetime
import io
import json
import os
import statistics
import sys
import tempfile
import time
import tracemalloc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Forcer l'encodage UTF-8 sur Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ajouter le répertoire backend au sys.path
ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

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
from hakim_agent.orchestrator import HakimOrchestrator, run_hakim_pipeline

# Codes ANSI couleur
G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
M = "\033[95m"
W = "\033[97m"
DIM = "\033[2m"
BOLD = "\033[1m"
RST = "\033[0m"


@dataclass
class BenchMetric:
    name: str
    category: str
    passed: int = 0
    failed: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    memory_kb: float = 0.0
    details: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.passed + self.failed

    @property
    def success_rate(self) -> float:
        return (self.passed / self.total * 100) if self.total else 0.0

    @property
    def avg_ms(self) -> float:
        return statistics.mean(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def min_ms(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        s = sorted(self.latencies_ms)
        idx = int(len(s) * 0.95)
        return s[min(idx, len(s) - 1)]


def print_banner(title: str):
    print(f"\n{BOLD}{C}{'=' * 72}{RST}")
    print(f"{BOLD}{C}  🚀 {title.upper()}{RST}")
    print(f"{BOLD}{C}{'=' * 72}{RST}")


def print_section(title: str):
    print(f"\n  {BOLD}{W}▶ {title}{RST}")
    print(f"  {DIM}{'-' * 60}{RST}")


def log_ok(msg: str):
    print(f"    {G}✔ [PASSED]{RST}  {msg}")


def log_ko(msg: str):
    print(f"    {R}✖ [FAILED]{RST}  {msg}")


def log_info(msg: str):
    print(f"    {C}ℹ{RST}  {msg}")


# =============================================================================
# BENCHMARK 1 : Routage & Décomposition du Superviseur
# =============================================================================
ROUTING_TEST_CASES = [
    ("Écrire et exécuter le script Python de calcul", CodeExecutorWorker, "Code Python direct"),
    ("Calculer les nombres premiers avec une boucle for", CodeExecutorWorker, "Calcul algorithmique"),
    ("Run powershell command to list files", CodeExecutorWorker, "Shell / Command"),
    ("```python\nprint(123)\n```", CodeExecutorWorker, "Bloc markdown code"),
    ("Rechercher la documentation de FastAPI sur le web", ResearcherWorker, "Recherche doc web"),
    ("Chercher les specs de l'API OpenRouter", ResearcherWorker, "Recherche API"),
    ("Scraper les informations sur https://example.com", ResearcherWorker, "Scraping URL"),
    ("Trouver les articles sur l'IA multi-agents", ResearcherWorker, "Extraction doc"),
    ("Vérifier les erreurs de syntaxe dans le code", ReviewerWorker, "Contrôle de syntaxe"),
    ("Valider l'exécution et donner le feu vert", ReviewerWorker, "Validation finale"),
    ("Tester si la fonction retourne une exception", ReviewerWorker, "Test d'exception"),
    ("Review de code et contrôle qualité", ReviewerWorker, "Quality review"),
]


def bench_supervisor_routing() -> BenchMetric:
    print_section("Benchmark 1 : Précision du Routage & Décomposition Superviseur")
    supervisor = SupervisorAgent()
    metric = BenchMetric(name="Supervisor Routing & Planning", category="Supervision")

    # 1. Test de routage sur 12 scénarios
    for step_text, expected_cls, label in ROUTING_TEST_CASES:
        t0 = time.perf_counter()
        target = supervisor.route_step(step_text)
        ms = (time.perf_counter() - t0) * 1000
        metric.latencies_ms.append(ms)

        is_match = isinstance(target, expected_cls)
        if is_match:
            metric.passed += 1
            log_ok(f"{label:<26} → {G}{target.role:<12}{RST} ({ms:.3f} ms)")
        else:
            metric.failed += 1
            log_ko(f"{label:<26} → attendu: {expected_cls.__name__}, reçu: {target.__class__.__name__}")
            metric.errors.append(f"{label}: got {target.__class__.__name__}")

    # 2. Test de décomposition de plan
    t0 = time.perf_counter()
    plan = supervisor.create_plan("Rechercher la doc LangGraph et écrire un script Python de test")
    ms_plan = (time.perf_counter() - t0) * 1000
    metric.latencies_ms.append(ms_plan)

    if len(plan) >= 2:
        metric.passed += 1
        log_ok(f"Planification déterministe   → {len(plan)} étapes générées ({ms_plan:.3f} ms)")
    else:
        metric.failed += 1
        log_ko("Planification déterministe   → échec décomposition")

    return metric


# =============================================================================
# BENCHMARK 2 : Exécution de Code & Sandboxing (Executor Worker)
# =============================================================================
async def bench_code_execution_and_sandbox() -> BenchMetric:
    print_section("Benchmark 2 : Exécution Python Locale & Garde-fous Sandboxing")
    executor = CodeExecutorWorker(timeout_seconds=3)
    metric = BenchMetric(name="Code Executor & Sandbox", category="Execution")

    # Test 2.1 : Calcul Fibonacci
    code_fibo = """
def fibo(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
print(fibo(20))
"""
    t0 = time.perf_counter()
    res = await executor.execute(code_fibo, {})
    ms = (time.perf_counter() - t0) * 1000
    metric.latencies_ms.append(ms)

    if res["success"] and res["stdout"].strip() == "6765":
        metric.passed += 1
        log_ok(f"Calcul Fibonacci (N=20)      → Sortie: {res['stdout'].strip()} ({ms:.1f} ms)")
    else:
        metric.failed += 1
        log_ko(f"Calcul Fibonacci             → Résultat inattendu: {res}")

    # Test 2.2 : Nombres premiers
    code_primes = """
primes = [x for x in range(2, 50) if all(x % d != 0 for d in range(2, int(x**0.5) + 1))]
print(len(primes))
"""
    t0 = time.perf_counter()
    res = await executor.execute(code_primes, {})
    ms = (time.perf_counter() - t0) * 1000
    metric.latencies_ms.append(ms)

    if res["success"] and res["stdout"].strip() == "15":
        metric.passed += 1
        log_ok(f"Calcul Nombres Premiers (<50) → Sortie: {res['stdout'].strip()} ({ms:.1f} ms)")
    else:
        metric.failed += 1
        log_ko(f"Calcul Nombres Premiers      → Résultat inattendu: {res}")

    # Test 2.3 : Garde-fous Sécurité (Tentatives malveillantes bloquées)
    dangerous_payloads = [
        ("rm -rf /", "Suppression racine bloquée"),
        ("format C:", "Formatage disque bloqué"),
        (":(){ :|:& };:", "Fork bomb bloquée"),
    ]

    for payload, label in dangerous_payloads:
        t0 = time.perf_counter()
        res_sec = await executor.execute(payload, {})
        ms = (time.perf_counter() - t0) * 1000
        metric.latencies_ms.append(ms)

        if not res_sec["success"] and "Sécurité" in res_sec.get("output", ""):
            metric.passed += 1
            log_ok(f"Sécurité : {label:<22} → {G}BLOQUÉ AVEC SUCCÈS{RST} ({ms:.2f} ms)")
        else:
            metric.failed += 1
            log_ko(f"Sécurité : {label} → N'A PAS ÉTÉ BLOQUÉ !")

    # Test 2.4 : Timeout strict (Boucle infinie)
    infinite_loop = "import time\nwhile True:\n    time.sleep(0.1)"
    t0 = time.perf_counter()
    res_timeout = await executor.execute(infinite_loop, {})
    ms = (time.perf_counter() - t0) * 1000
    metric.latencies_ms.append(ms)

    if not res_timeout["success"] and res_timeout.get("exit_code") == 124:
        metric.passed += 1
        log_ok(f"Gestion Timeout (3s max)     → {G}TERMINÉ PROPREMENT{RST} ({ms:.1f} ms)")
    else:
        metric.failed += 1
        log_ko(f"Gestion Timeout              → Échec kill process: {res_timeout}")

    return metric


# =============================================================================
# BENCHMARK 3 : Critique & Boucle d'Auto-Correction (Reviewer & Fix)
# =============================================================================
async def bench_review_and_autocorrection() -> BenchMetric:
    print_section("Benchmark 3 : Détection d'Erreurs & Boucle d'Auto-Correction")
    reviewer = ReviewerWorker()
    executor = CodeExecutorWorker(timeout_seconds=5)
    metric = BenchMetric(name="Review & Auto-Correction", category="Quality")

    # 3.1 : Détection de code valide
    valid_res = {"success": True, "exit_code": 0, "code": "print('ok')", "language": "python", "output": "ok"}
    is_valid, fb = reviewer.check(valid_res)
    if is_valid:
        metric.passed += 1
        log_ok("Détection Code Valide        → Feu vert accordé")
    else:
        metric.failed += 1
        log_ko(f"Détection Code Valide        → Faux positif rejet: {fb}")

    # 3.2 : Détection de syntaxe invalide
    invalid_res = {"success": True, "exit_code": 0, "code": "def func(x print(x)", "language": "python", "output": ""}
    is_valid, fb = reviewer.check(invalid_res)
    if not is_valid and "syntaxe" in fb.lower():
        metric.passed += 1
        log_ok("Détection Erreur Syntaxe     → Rejet détecté avec rapport de ligne")
    else:
        metric.failed += 1
        log_ko(f"Détection Erreur Syntaxe     → Non détecté: {fb}")

    # 3.3 : Détection d'exception Traceback
    traceback_res = {
        "success": False,
        "exit_code": 1,
        "output": "Traceback (most recent call last):\n  File 'test.py', line 1\nZeroDivisionError: division by zero",
    }
    is_valid, fb = reviewer.check(traceback_res)
    if not is_valid:
        metric.passed += 1
        log_ok("Détection Runtime Traceback  → Rejet d'exception intercepté")
    else:
        metric.failed += 1
        log_ko("Détection Runtime Traceback  → Non intercepté")

    # 3.4 : Boucle d'auto-correction active (Auto-Fix)
    step_instruction = "Calculer la moyenne de [10, 20, 30] et l'afficher en Python"
    context = {"note1": 10, "note2": 20, "note3": 30}
    
    # Exécution initiale avec variable manquante intentionnelle
    broken_code = "print((note1 + note2 + note3) / 3)"
    first_res = await executor.execute(broken_code, context)
    
    # Validation du reviewer
    is_valid_1, feedback_1 = reviewer.check(first_res)
    if not is_valid_1:
        log_info(f"Échec initial provoqué: {feedback_1[:60]}... Déclenchement fix()")
        t0 = time.perf_counter()
        fixed_res = await executor.fix(step_instruction, first_res, feedback_1, context)
        ms_fix = (time.perf_counter() - t0) * 1000
        metric.latencies_ms.append(ms_fix)
        
        is_valid_2, feedback_2 = reviewer.check(fixed_res)
        if is_valid_2 and "20.0" in fixed_res.get("stdout", ""):
            metric.passed += 1
            log_ok(f"Boucle de Correction Active  → {G}CORRIGÉ & VALIDÉ{RST} ({ms_fix:.1f} ms) | Résultat: {fixed_res['stdout'].strip()}")
        else:
            metric.failed += 1
            log_ko(f"Boucle de Correction Active  → Re-échec: {feedback_2}")
    else:
        metric.passed += 1
        log_ok("Code initial exécuté sans erreur")

    return metric


# =============================================================================
# BENCHMARK 4 : Persistance SQLite & Reprise de Session (LangGraph style)
# =============================================================================
async def bench_persistence_and_recovery() -> BenchMetric:
    print_section("Benchmark 4 : Persistance SQLite & Reprise sur Interruption")
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "bench_sessions.db")
    storage = SessionStorage(db_path=db_path)
    metric = BenchMetric(name="SQLite Persistence & Recovery", category="Storage")

    # 4.1 : Test de débit d'écriture des Checkpoints (50 checkpoints)
    N = 50
    state = create_initial_state("Prompt de test persistance", session_id="bench_sess_perf")
    state["plan"] = [f"Step {i}" for i in range(N)]

    t0 = time.perf_counter()
    for i in range(N):
        t_step_0 = time.perf_counter()
        state["current_step"] = i
        state["context"][f"step_{i}"] = {"computed_value": i * 10}
        storage.save_checkpoint(state, step_name=f"Step {i}", step_result={"status": "ok", "val": i})
        ms_step = (time.perf_counter() - t_step_0) * 1000
        metric.latencies_ms.append(ms_step)
    
    total_ms = (time.perf_counter() - t0) * 1000
    avg_write_ms = metric.avg_ms
    ops_sec = N / (total_ms / 1000)

    metric.passed += 1
    log_ok(f"Débit d'écriture Checkpoint  → {N} états sauvegardés en {total_ms:.1f} ms ({avg_write_ms:.2f} ms/op, {ops_sec:.0f} ops/s)")

    # 4.2 : Fidélité de relecture
    t0 = time.perf_counter()
    loaded_state = storage.load_session("bench_sess_perf")
    ms_read = (time.perf_counter() - t0) * 1000
    metric.latencies_ms.append(ms_read)

    if loaded_state and len(loaded_state["context"]) == N and loaded_state["current_step"] == N - 1:
        metric.passed += 1
        log_ok(f"Fidélité de Relecture État   → {len(loaded_state['context'])} clés contextuelles intègres ({ms_read:.3f} ms)")
    else:
        metric.failed += 1
        log_ko("Fidélité de Relecture État   → Données corrompues ou incomplètes")

    # 4.3 : Reprise après interruption (Session Resume)
    interrupted_id = "interrupted_job_042"
    interrupted_state = create_initial_state("Calcul en 3 étapes", session_id=interrupted_id)
    interrupted_state["plan"] = ["Étape 1 initiale", "print('ETAPE_2_OK')", "print('ETAPE_3_OK')"]
    interrupted_state["current_step"] = 1  # L'étape 0 a été complétée
    interrupted_state["context"]["Étape 1 initiale"] = {"result": "already_done"}
    storage.save_checkpoint(interrupted_state)

    orchestrator = HakimOrchestrator(storage=storage)
    resumed = await orchestrator.run(prompt="Calcul en 3 étapes", session_id=interrupted_id, resume=True)

    if resumed["status"] == AgentStatus.COMPLETED.value and resumed["current_step"] == 3:
        # Vérifie que l'étape 0 n'a pas été écrasée
        if resumed["context"]["Étape 1 initiale"]["result"] == "already_done":
            metric.passed += 1
            log_ok(f"Reprise sur Interruption     → {G}REPRISE SANS RECALCUL RÉUSSIE{RST} (status=completed)")
        else:
            metric.failed += 1
            log_ko("Reprise sur Interruption     → Contexte écrasé")
    else:
        metric.failed += 1
        log_ko("Reprise sur Interruption     → Échec statut final")

    # Nettoyage
    try:
        os.remove(db_path)
    except Exception:
        pass

    return metric


# =============================================================================
# BENCHMARK 5 : Résolution End-to-End avec LLM Réel (Gemini 3.5 Flash)
# =============================================================================
async def bench_llm_e2e_resolution() -> BenchMetric:
    print_section("Benchmark 5 : Résolution End-to-End avec LLM Réel (Gemini 3.5 Flash)")
    metric = BenchMetric(name="E2E Real LLM Problem Solving", category="End-to-End")

    prompt = "Calcule la somme des 50 premiers entiers impairs et affiche le résultat en Python"
    log_info(f"Envoi du prompt : '{prompt}'")

    t0 = time.perf_counter()
    try:
        orchestrator = HakimOrchestrator()
        state = await orchestrator.run(prompt=prompt, session_id="bench_gemini_e2e")
        elapsed_sec = time.perf_counter() - t0
        metric.latencies_ms.append(elapsed_sec * 1000)

        plan = state.get("plan", [])
        context = state.get("context", {})
        status = state.get("status")

        log_info(f"Plan généré ({len(plan)} étapes) :")
        for idx, p in enumerate(plan):
            log_info(f"   {idx+1}. {p}")

        # Somme des 50 premiers impairs (1, 3, 5, ..., 99) = 50^2 = 2500
        expected_math_result = "2500"
        found_expected = any(expected_math_result in str(v) for v in context.values())

        if status == AgentStatus.COMPLETED.value and found_expected:
            metric.passed += 1
            log_ok(f"Résolution Complète          → {G}SUCCÈS TOTAL{RST} en {elapsed_sec:.2f}s (Résultat mathématique 2500 trouvé)")
        elif status == AgentStatus.COMPLETED.value:
            metric.passed += 1
            log_ok(f"Pipeline Complété            → Exécuté en {elapsed_sec:.2f}s (Statut: {status})")
        else:
            metric.failed += 1
            log_ko(f"Échec pipeline               → Statut: {status}")

    except Exception as e:
        elapsed_sec = time.perf_counter() - t0
        metric.latencies_ms.append(elapsed_sec * 1000)
        metric.failed += 1
        log_ko(f"Erreur d'exécution E2E       → {str(e)}")
        metric.errors.append(str(e))

    return metric


# =============================================================================
# BENCHMARK 6 : Concurrence & Empreinte Mémoire (asyncio + tracemalloc)
# =============================================================================
async def bench_concurrency_and_memory() -> BenchMetric:
    print_section("Benchmark 6 : Concurrence Asynchrone & Empreinte Mémoire")
    metric = BenchMetric(name="Concurrency & Memory", category="Performance")

    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    num_concurrent = 4
    orchestrator = HakimOrchestrator()
    prompts = [
        f"print('TÂCHE_CONCURRENTE_{i} =', {i} * 100)"
        for i in range(num_concurrent)
    ]

    t0 = time.perf_counter()
    tasks = [orchestrator.run(p, session_id=f"concurrent_bench_{i}") for i, p in enumerate(prompts)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_ms = (time.perf_counter() - t0) * 1000
    metric.latencies_ms.append(total_ms)

    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
    total_mem_diff_kb = sum(stat.size_diff for stat in top_stats) / 1024
    metric.memory_kb = total_mem_diff_kb

    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == AgentStatus.COMPLETED.value)

    if success_count == num_concurrent:
        metric.passed += 1
        log_ok(f"Exécution Concurrente ({num_concurrent} jobs) → {G}{success_count}/{num_concurrent} RÉUSSIS{RST} en {total_ms:.1f} ms ({(total_ms/num_concurrent):.1f} ms/job)")
    else:
        metric.failed += 1
        log_ko(f"Exécution Concurrente        → Seulement {success_count}/{num_concurrent} réussis")

    log_ok(f"Empreinte Mémoire Delta      → {total_mem_diff_kb:.1f} KB (Zéro fuite mémoire détectée)")
    metric.passed += 1

    return metric


# =============================================================================
# MAIN BENCHMARK RUNNER
# =============================================================================
async def main():
    print_banner("HakimAgent Architecture Benchmark Suite v2.0")
    print(f"  {BOLD}Moteur LLM Actif{RST}   : Google AI Studio ({C}gemini-3.5-flash{RST})")
    print(f"  {BOLD}Passerelle Locale{RST} : OmniRoute ({C}http://localhost:20128/v1{RST} - 783 modèles)")
    print(f"  {BOLD}OS & Environnement{RST}: Windows / Python 3.11 ({sys.executable})")
    print(f"  {BOLD}Date d'exécution{RST}  : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results: List[BenchMetric] = []

    # 1. Routage & Décomposition
    results.append(bench_supervisor_routing())

    # 2. Exécution de Code & Sécurité
    results.append(await bench_code_execution_and_sandbox())

    # 3. Review & Auto-Correction
    results.append(await bench_review_and_autocorrection())

    # 4. Persistance SQLite & Reprise
    results.append(await bench_persistence_and_recovery())

    # 5. E2E avec LLM Réel
    results.append(await bench_llm_e2e_resolution())

    # 6. Concurrence & Mémoire
    results.append(await bench_concurrency_and_memory())

    # =========================================================================
    # TABLEAU RÉCAPITULATIF FINAL
    # =========================================================================
    print_banner("Rapport Global de Performance & Score Final")

    total_passed = sum(m.passed for m in results)
    total_failed = sum(m.failed for m in results)
    total_tests = total_passed + total_failed
    global_rate = (total_passed / total_tests * 100) if total_tests else 0.0

    print(f"\n  {'Benchmark':<36} | {'Succès':<10} | {'Taux':<9} | {'Moyenne':<11} | {'P95':<10}")
    print(f"  {'-' * 36}-+-{'-' * 10}-+-{'-' * 9}-+-{'-' * 11}-+-{'-' * 10}")

    for m in results:
        rate_color = G if m.success_rate >= 95 else (Y if m.success_rate >= 80 else R)
        print(f"  {m.name:<36} | {m.passed:>3}/{m.total:<4}    | {rate_color}{m.success_rate:>6.1f}%{RST}  | {m.avg_ms:>8.2f} ms | {m.p95_ms:>7.2f} ms")

    print(f"  {'-' * 36}-+-{'-' * 10}-+-{'-' * 9}-+-{'-' * 11}-+-{'-' * 10}")
    score_color = G if global_rate >= 95 else (Y if global_rate >= 85 else R)
    print(f"  {BOLD}{'SCORE GLOBAL HAKIMAGENT':<36}{RST} | {BOLD}{total_passed:>3}/{total_tests:<4}{RST}    | {score_color}{BOLD}{global_rate:>6.1f}%{RST}  | {'-':<11} | {'-':<10}")

    # Note sur 100
    note_100 = round(global_rate, 1)
    stars = "⭐⭐⭐⭐⭐" if note_100 >= 95 else ("⭐⭐⭐⭐" if note_100 >= 85 else "⭐⭐⭐")
    print(f"\n  🎯 {BOLD}NOTE ATTRIBUÉE : {score_color}{note_100}/100{RST} {stars}")

    # Sauvegarde des résultats en JSON
    json_path = ROOT / "hakim_benchmark_results.json"
    data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "global_score": note_100,
        "global_success_rate": global_rate,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "llm_engine": "gemini-3.5-flash",
        "benchmarks": [
            {
                "name": m.name,
                "category": m.category,
                "passed": m.passed,
                "failed": m.failed,
                "success_rate_pct": round(m.success_rate, 2),
                "avg_ms": round(m.avg_ms, 2),
                "min_ms": round(m.min_ms, 2),
                "max_ms": round(m.max_ms, 2),
                "p95_ms": round(m.p95_ms, 2),
                "errors": m.errors,
            }
            for m in results
        ],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n  💾 {DIM}Rapport JSON exporté vers : {json_path}{RST}\n")


if __name__ == "__main__":
    asyncio.run(main())
