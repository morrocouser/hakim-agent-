#!/usr/bin/env python3
"""
Test complet de validation du Circuit Breaker et du Repli Dynamique pour AXIOM.
Valide:
1. Les transitions d'états (CLOSED -> OPEN -> HALF_OPEN -> CLOSED).
2. L'ouverture immédiate sur code HTTP 429 (Rate Limit).
3. L'échelle de repli (Fallback Ladder) dans scoring.py.
4. Le traitement du Tier 3 (Dégradation Gracieuse) dans ErrorProtocol.
5. La simulation de bout en bout de la bascule vers le modèle de secours.
"""

import sys
import os
import time
import asyncio

# S'assurer que le backend est accessible dans sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from axiom.core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerRegistry,
    CircuitBreakerOpenException,
    LLMServiceUnavailableError,
    circuit_breakers,
)
from axiom.models.schemas import ModelName, AgentName, TaskAssignment, ScoringDimensions
from axiom.core.scoring import (
    MODEL_FALLBACK_LADDER,
    get_fallback_model,
    select_model,
)
from axiom.core.error_protocol import ErrorProtocol, ErrorTier
from axiom.tools.error_log import ErrorLog
from axiom.core.memory import MemoryManager


def test_circuit_breaker_transitions():
    print("🧪 Test 1 : Machine à états du CircuitBreaker (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)...")
    cb = CircuitBreaker("test-service", failure_threshold=2, recovery_timeout=0.2)
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # 1er échec : reste CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # 2e échec : atteint le seuil -> bascule en OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False
    print("  ✅ Fermeture normale -> Ouverture après 2 échecs validée")

    # Attente du cooldown (0.2s)
    time.sleep(0.25)
    # can_execute doit déclencher la transition vers HALF_OPEN
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN
    print("  ✅ Expiration du cooldown -> Transition vers HALF_OPEN validée")

    # Succès en HALF_OPEN -> retour en CLOSED
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.can_execute() is True
    print("  ✅ Succès de sonde en HALF_OPEN -> Rétablissement en CLOSED validé")


def test_circuit_breaker_rate_limit_fast_trip():
    print("\n🧪 Test 2 : Déclenchement immédiat sur HTTP 429 (Rate Limit)...")
    cb = CircuitBreaker("test-rate-limit", failure_threshold=5, recovery_timeout=1.0)
    assert cb.state == CircuitState.CLOSED

    # Enregistrement d'un 429 -> ouverture immédiate sans attendre 5 échecs
    cb.record_failure(is_rate_limit=True)
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False
    print("  ✅ Déclenchement immédiat (Fast Trip) sur 429 validé")


def test_circuit_breaker_registry():
    print("\n🧪 Test 3 : Fonctionnement du CircuitBreakerRegistry (Singleton)...")
    reg1 = CircuitBreakerRegistry()
    reg2 = CircuitBreakerRegistry()
    assert reg1 is reg2

    reg1.reset_all()
    b1 = reg1.get_or_create("llm:test-model", failure_threshold=3)
    assert b1.name == "llm:test-model"
    assert reg1.is_available("llm:test-model") is True

    b1.record_failure(is_rate_limit=True)
    assert reg1.is_available("llm:test-model") is False

    summary = reg1.get_status_summary()
    assert "llm:test-model" in summary
    assert summary["llm:test-model"]["state"] == "OPEN"
    print("  ✅ Registre centralisé et résumé d'état validés")


def test_scoring_fallback_ladder():
    print("\n🧪 Test 4 : Échelle de repli dynamique (scoring.py)...")
    reg = CircuitBreakerRegistry()
    reg.reset_all()

    best_model = ModelName.BEST.value
    expected_next = MODEL_FALLBACK_LADDER[best_model][0]

    # Quand le modèle BEST est disponible
    fallback_model, is_fallback = get_fallback_model(best_model, reg)
    assert fallback_model == expected_next
    print(f"  ✅ Repli initial configuré : {best_model} -> {expected_next}")

    # Ouvrir le disjoncteur du modèle BEST et du 1er repli
    reg.get_or_create(f"llm:{best_model}").record_failure(is_rate_limit=True)
    reg.get_or_create(f"llm:{expected_next}").record_failure(is_rate_limit=True)

    # select_model doit éviter BEST car son circuit est ouvert
    dims = ScoringDimensions(complexity=9.0, stakes=9.0)  # Normalement routé vers BEST
    routed_model = select_model(9.5, dims, check_breaker=True)
    assert routed_model.value != best_model
    assert routed_model.value != expected_next
    print(f"  ✅ select_model a contourné les modèles en panne vers : {routed_model.value}")


def test_error_protocol_graceful_degradation():
    print("\n🧪 Test 5 : Protocole d'Erreur Tier 3 (Dégradation Gracieuse & Repli)...")
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        temp_log = f.name

    try:
        error_log = ErrorLog(temp_log)
        memory = MemoryManager()
        proto = ErrorProtocol(error_log, memory)

        # Disjoncteur initialement réinitialisé
        circuit_breakers.reset_all()

        task = TaskAssignment(
            task_id="T_TEST01",
            description="Tâche de test avec modèle saturé",
            agent=AgentName.CODER,
            model=ModelName.BEST,
            score=8.5,
            dimensions=ScoringDimensions(),
        )

        # Simuler une erreur 429 levée par l'API
        err = LLMServiceUnavailableError("HTTP 429: Too Many Requests", status_code=429, model=ModelName.BEST.value)
        
        # Classification
        tier = proto._classify_error(err, task, "context de test", iteration=1)
        assert tier == ErrorTier.GRACEFUL_DEGRADATION
        print("  ✅ Classification immédiate en TIER_3 (GRACEFUL_DEGRADATION) validée")

        # Exécution du handler
        result = asyncio.run(proto.handle_error(err, task, "context de test", iteration=1))
        assert result.handled is True
        assert result.should_continue is True
        assert result.modified_task is not None
        assert result.modified_task.model != ModelName.BEST
        print(f"  ✅ Substitution de tâche validée : nouveau modèle = {result.modified_task.model}")
        print(f"  ✅ Message utilisateur : \n{result.user_message}")

        # Vérifier que le disjoncteur de BEST a bien été ouvert
        assert circuit_breakers.is_available(f"llm:{ModelName.BEST.value}") is False
        print("  ✅ Disjoncteur de BEST confirmé OPEN après traitement de l'erreur")

    finally:
        if os.path.exists(temp_log):
            os.remove(temp_log)


def run_all():
    print("=" * 70)
    print("🚀 DÉMARRAGE DU SUITE DE VALIDATION DU CIRCUIT BREAKER AXIOM")
    print("=" * 70)
    test_circuit_breaker_transitions()
    test_circuit_breaker_rate_limit_fast_trip()
    test_circuit_breaker_registry()
    test_scoring_fallback_ladder()
    test_error_protocol_graceful_degradation()
    print("\n" + "=" * 70)
    print("🎉 TOUS LES TESTS DU CIRCUIT BREAKER SONT PASSÉS AVEC SUCCÈS !")
    print("=" * 70)


if __name__ == "__main__":
    run_all()
