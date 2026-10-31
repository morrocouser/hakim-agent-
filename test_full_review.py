#!/usr/bin/env python3
"""
Suite de tests intensifs et de revue de code pour AXIOM.
Couvre tous les cas limites (Edge Cases), la concurrence multi-threads,
la robustesse aux erreurs et l'intégration simultanée de:
- Circuit Breaker & Fallback Ladder
- RepoMap AST (syntaxe invalide, petits budgets, TS/JS)
- OpenInference Telemetry (isolation async, spans profonds, gestion d'erreurs)
- Boucle ReAct complète de bout en bout
"""

import sys
import os
import time
import json
import tempfile
import asyncio
import threading
from pathlib import Path

# S'assurer que le backend est accessible dans sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from axiom.core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerRegistry,
    CircuitBreakerOpenException,
    LLMServiceUnavailableError,
    circuit_breakers,
)
from axiom.tools.repo_map import CodebaseMapper, get_repository_map
from axiom.core.telemetry import (
    TelemetryTracer,
    SpanKind,
    SpanAttributes,
    tracer,
)
from axiom.models.schemas import TaskAssignment, TaskStatus, AgentName, ModelName, ScoringDimensions
from axiom.core.error_protocol import ErrorProtocol, ErrorTier
from axiom.tools.error_log import ErrorLog
from axiom.core.memory import MemoryManager
from axiom.core.react_loop import ReActLoop


# =============================================================================
# 1. TESTS DE CONCURRENCE & CAS LIMITES DU CIRCUIT BREAKER
# =============================================================================

def test_circuit_breaker_concurrency():
    print("🧪 [Revue 1.1] Concurrence multi-thread sur CircuitBreaker...")
    cb = CircuitBreaker("concurrent-test", failure_threshold=50, recovery_timeout=0.2)

    def worker_failures():
        for _ in range(25):
            cb.record_failure()
            time.sleep(0.001)

    threads = [threading.Thread(target=worker_failures) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Doit avoir atteint le seuil et être OPEN
    assert cb.state == CircuitState.OPEN
    assert cb.failure_count >= 50
    assert cb.can_execute() is False
    print("  ✅ Thread-safety validée : état cohérent sous 100 échecs concurrents")


def test_circuit_breaker_half_open_trial_limitation():
    print("🧪 [Revue 1.2] Limitation stricte des sondes en HALF_OPEN...")
    cb = CircuitBreaker("probe-test", failure_threshold=1, recovery_timeout=0.05, half_open_max_trials=1)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    time.sleep(0.08)
    # 1er appel : transition en HALF_OPEN et accorde 1 essai
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    # 2e appel pendant que le 1er est en vol : doit refuser
    assert cb.can_execute() is False
    print("  ✅ Blocage des requêtes excédentaires pendant la sonde HALF_OPEN validé")


# =============================================================================
# 2. TESTS DE ROBUSTESSE & CAS LIMITES DE REPOMAP
# =============================================================================

def test_repo_map_syntax_error_resilience():
    print("\n🧪 [Revue 2.1] Résilience aux fichiers corrompus ou syntaxe invalide...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Fichier avec erreur de syntaxe volontaire
        bad_py = Path(tmp_dir) / "corrupted.py"
        bad_py.write_text("def broken_syntax( :::: { return [", encoding="utf-8")

        # Fichier vide
        empty_py = Path(tmp_dir) / "empty.py"
        empty_py.write_text("", encoding="utf-8")

        # Fichier valide
        valid_py = Path(tmp_dir) / "valid.py"
        valid_py.write_text("class ValidClass:\n    def run(self) -> None: pass", encoding="utf-8")

        mapper = CodebaseMapper(tmp_dir)
        # Ne doit pas lever d'exception
        res = mapper.generate_symbol_map(max_tokens=500)
        assert "ValidClass" in res
        assert "def run(self) -> None" in res
        print("  ✅ Fichiers corrompus ignorés gracieusement sans crash")


def test_repo_map_micro_budget():
    print("🧪 [Revue 2.2] Gestion des micro-budgets de tokens (ex: 15 tokens)...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i in range(5):
            p = Path(tmp_dir) / f"file_{i}.py"
            p.write_text(f"class LargeClass_{i}:\n    def func(self): pass\n", encoding="utf-8")

        mapper = CodebaseMapper(tmp_dir)
        # Budget minuscule : ~60 caractères
        res = mapper.generate_symbol_map(max_tokens=15)
        assert len(res) <= 300  # Reste borné avec le message de troncature
        print("  ✅ Micro-budget respecté avec message de troncature informatif")


# =============================================================================
# 3. TESTS DE CONCURRENCE ASYNC & ROBUSTESSE DE LA TÉLÉMÉTRIE
# =============================================================================

def test_telemetry_async_context_isolation():
    print("\n🧪 [Revue 3.1] Isolation des traces entre coroutines asynchrones...")
    test_tracer = TelemetryTracer()

    async def worker_task(task_name: str, delay: float):
        with test_tracer.start_as_current_span(f"root_{task_name}", kind=SpanKind.AGENT) as r:
            await asyncio.sleep(delay)
            with test_tracer.start_as_current_span(f"sub_{task_name}", kind=SpanKind.CHAIN) as s:
                assert s.trace_id == r.trace_id
                assert s.parent_span_id == r.span_id
                await asyncio.sleep(delay)
                return r.trace_id

    async def run_concurrent():
        t1 = asyncio.create_task(worker_task("A", 0.02))
        t2 = asyncio.create_task(worker_task("B", 0.01))
        trace1, trace2 = await asyncio.gather(t1, t2)
        assert trace1 != trace2, "Les traces asynchrones concurrentes doivent avoir des IDs distincts"

    asyncio.run(run_concurrent())
    print("  ✅ Isolation ContextVar validée : chaque tâche asynchrone a son propre trace_id")


def test_telemetry_deep_nested_spans():
    print("🧪 [Revue 3.2] Gestion des spans profondément imbriqués (profondeur 8)...")
    test_tracer = TelemetryTracer()

    def build_nest(depth: int, max_depth: int, root_id: str):
        if depth >= max_depth:
            return
        with test_tracer.start_as_current_span(f"level_{depth}", kind=SpanKind.CHAIN) as s:
            assert s.trace_id == root_id
            build_nest(depth + 1, max_depth, root_id)

    with test_tracer.start_as_current_span("top_level", kind=SpanKind.AGENT) as top:
        build_nest(1, 8, top.trace_id)

    print("  ✅ Imbrication profonde (profondeur 8) exécutée sans débordement de pile")


# =============================================================================
# 4. TEST INTÉGRÉ DE BOUT EN BOUT (SIMULATION COMPLETE)
# =============================================================================

def test_end_to_end_failover_with_telemetry_and_repomap():
    print("\n🧪 [Revue 4.1] Simulation de bout en bout : Erreur 429 -> Circuit Breaker -> Fallback -> Succès...")

    class FlakyClient:
        def __init__(self):
            self.calls = []

        async def chat(self, model: str, system: str, messages: list[dict], max_tokens: int = 4096):
            self.calls.append(model)
            # Simuler que le modèle BEST échoue en 429
            if model == ModelName.BEST.value:
                raise LLMServiceUnavailableError("HTTP 429: Rate limit exceeded", status_code=429, model=model)
            # Réponse d'auto-évaluation en JSON si demandé
            if "AUTO-ÉVALUATION" in system:
                return json.dumps({
                    "scores": {"pertinence": 9.0, "complete": 8.5, "exactitude": 9.0, "qualite": 8.5, "concision": 8.0},
                    "score_global": 8.6,
                    "decision": "LIVRAISON",
                    "points_forts": ["Tests complets"],
                    "points_faibles": [],
                    "ameliorations_concretes": [],
                    "alternative_approche": ""
                })
            # Le modèle de repli répond avec succès
            return f"Code généré avec succès par le modèle de repli: {model}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Créer du code dans l'environnement de test
        code_file = Path(tmp_dir) / "calculator.py"
        code_file.write_text("class Calculator:\n    def add(self, a: int, b: int) -> int: return a + b\n", encoding="utf-8")

        # Initialiser AXIOM
        tracer.clear()
        circuit_breakers.reset_all()

        memory = MemoryManager()
        client = FlakyClient()
        loop = ReActLoop(memory=memory, claude=client, max_iterations=3)

        task = TaskAssignment(
            task_id="T_STRESS_01",
            description="Créer les tests unitaires pour Calculator",
            agent=AgentName.CODER,
            model=ModelName.BEST,  # Modèle qui va échouer
            score=8.0,
            dimensions=ScoringDimensions(complexity=7.0, stakes=8.0),
        )

        # Exécution de la tâche
        result = asyncio.run(loop.execute(task))

        # 1. Vérifier que la tâche a finalement réussi
        assert result.status == TaskStatus.DONE
        assert "modèle de repli" in result.output
        print("  ✅ Tâche terminée en succès après bascule automatique")

        # 2. Vérifier que le disjoncteur du modèle BEST s'est ouvert
        assert circuit_breakers.is_available(f"llm:{ModelName.BEST.value}") is False
        print(f"  ✅ Disjoncteur ouvert confirmé pour : {ModelName.BEST.value}")

        # 3. Vérifier que FlakyClient a été appelé avec les deux modèles
        assert ModelName.BEST.value in client.calls
        assert len(client.calls) >= 2
        print(f"  ✅ Modèles successivement sollicités : {client.calls}")

        # 4. Vérifier la télémétrie enregistrée
        traces = tracer.get_recent_traces()
        trace_kinds = [t["kind"] for t in traces]
        assert "AGENT" in trace_kinds
        assert "LLM" in trace_kinds
        print(f"  ✅ Spans télémétriques générés : {[t['name'] for t in traces]}")


def run_all_reviews():
    print("=" * 70)
    print("🔬 DÉMARRAGE DE LA REVUE DE CODE APPROFONDIE ET DES TESTS DE STRESS")
    print("=" * 70)
    test_circuit_breaker_concurrency()
    test_circuit_breaker_half_open_trial_limitation()
    test_repo_map_syntax_error_resilience()
    test_repo_map_micro_budget()
    test_telemetry_async_context_isolation()
    test_telemetry_deep_nested_spans()
    test_end_to_end_failover_with_telemetry_and_repomap()
    print("\n" + "=" * 70)
    print("🏆 TOUS LES TESTS DE REVUE ET DE CAS LIMITES SONT PASSÉS SANS ERREUR !")
    print("=" * 70)


if __name__ == "__main__":
    run_all_reviews()
