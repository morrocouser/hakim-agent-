"""
AXIOM v4.0 — Disjoncteur (Circuit Breaker) et Gestion de Résilience.

Fournit une machine à états (CLOSED, OPEN, HALF_OPEN) pour isoler les services
défaillants (API LLM, outils externes de recherche, APIs distantes) et déclencher
automatiquement un repli sans bloquer la boucle d'exécution de l'agent.
"""

from __future__ import annotations

import time
import threading
from enum import Enum
from typing import Dict, Optional, Any
from axiom.logging_setup import log


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # Opération normale, requêtes autorisées
    OPEN = "OPEN"            # Service en panne, requêtes rejetées immédiatement
    HALF_OPEN = "HALF_OPEN"  # Période d'essai, sonde envoyée pour vérifier le rétablissement


class CircuitBreakerOpenException(Exception):
    """Levée lorsqu'une requête est tentée alors que le disjoncteur est ouvert."""
    def __init__(self, service_name: str, cooldown_remaining: float):
        self.service_name = service_name
        self.cooldown_remaining = max(0.0, cooldown_remaining)
        super().__init__(
            f"Circuit ouvert pour '{service_name}'. "
            f"Récupération estimée dans {self.cooldown_remaining:.1f}s."
        )


class LLMServiceUnavailableError(Exception):
    """Levée lorsqu'un service LLM externe échoue (429, 502, 503, 504, timeout)."""
    def __init__(self, message: str, status_code: Optional[int] = None, model: Optional[str] = None):
        self.status_code = status_code
        self.model = model
        super().__init__(message)


class CircuitBreaker:
    """
    Disjoncteur individuel surveillant un service ou modèle spécifique.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        half_open_max_trials: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_trials = half_open_max_trials

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.consecutive_successes = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()
        self._half_open_trials = 0
        self._lock = threading.RLock()

    def can_execute(self) -> bool:
        """
        Détermine si une exécution vers ce service est autorisée.
        Gère la transition automatique OPEN -> HALF_OPEN à l'expiration du cooldown.
        """
        with self._lock:
            # Filets de sécurité ultimes : ne jamais bloquer indéfiniment
            if any(k in self.name for k in ("gemini-3.5-flash", "local:default", "auto/best-fast")):
                return True

            now = time.time()

            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                if self.last_failure_time and (now - self.last_failure_time >= self.recovery_timeout):
                    log.info("🔌 CircuitBreaker [%s]: Période de refroidissement expirée -> Passage en HALF_OPEN", self.name)
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = now
                    self._half_open_trials = 1
                    return True
                return False

            if self.state == CircuitState.HALF_OPEN:
                # Si le temps d'attente dépasse recovery_timeout sans succès ni échec, reset du cycle d'essai
                if self.last_state_change and (now - self.last_state_change >= self.recovery_timeout):
                    self._half_open_trials = 1
                    self.last_state_change = now
                    return True

                # N'autorise qu'un nombre restreint d'essais pendant HALF_OPEN
                if self._half_open_trials < self.half_open_max_trials:
                    self._half_open_trials += 1
                    return True
                return False

            return False

    def remaining_cooldown(self) -> float:
        """Retourne le temps restant en secondes avant la tentative de réouverture."""
        with self._lock:
            if self.state != CircuitState.OPEN or not self.last_failure_time:
                return 0.0
            elapsed = time.time() - self.last_failure_time
            return max(0.0, self.recovery_timeout - elapsed)

    def record_success(self) -> None:
        """Enregistre un succès et réinitialise le circuit en mode CLOSED."""
        with self._lock:
            now = time.time()
            self.failure_count = 0
            self._half_open_trials = 0

            if self.state != CircuitState.CLOSED:
                log.info("🔌 CircuitBreaker [%s]: Succès confirmé -> Fermeture du circuit (CLOSED)", self.name)
                self.state = CircuitState.CLOSED
                self.last_state_change = now

    def record_failure(self, error: Optional[Exception] = None, is_rate_limit: bool = False) -> None:
        """
        Enregistre un échec.
        En cas de Rate Limit (HTTP 429), le disjoncteur bascule immédiatement en OPEN.
        """
        with self._lock:
            now = time.time()
            self.last_failure_time = now

            if is_rate_limit:
                # Quota / 429 : fermeture immédiate pour éviter de spammer le serveur
                self.failure_count = self.failure_threshold
                self.state = CircuitState.OPEN
                self.last_state_change = now
                log.warning(
                    "🔌 CircuitBreaker [%s]: Dépassement de quota/429 détecté -> DISJONCTEUR OUVERT (cooldown: %ss)",
                    self.name, self.recovery_timeout
                )
                return

            self.failure_count += 1

            if self.state == CircuitState.HALF_OPEN:
                # Un échec lors de l'essai replonge immédiatement en OPEN
                self.state = CircuitState.OPEN
                self.last_state_change = now
                log.warning("🔌 CircuitBreaker [%s]: Échec du test en HALF_OPEN -> Réouverture du disjoncteur", self.name)
            elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.last_state_change = now
                log.warning(
                    "🔌 CircuitBreaker [%s]: Seuil d'échecs atteint (%s/%s) -> DISJONCTEUR OUVERT (cooldown: %ss)",
                    self.name, self.failure_count, self.failure_threshold, self.recovery_timeout
                )

    def reset(self) -> None:
        """Réinitialise manuellement le disjoncteur en état CLOSED."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self._half_open_trials = 0
            self.last_failure_time = None
            self.last_state_change = time.time()

    def get_status(self) -> Dict[str, Any]:
        """Retourne un dictionnaire d'état pour les diagnostics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "remaining_cooldown": round(self.remaining_cooldown(), 1),
                "recovery_timeout": self.recovery_timeout,
            }


class CircuitBreakerRegistry:
    """
    Registre centralisant tous les disjoncteurs du système AXIOM.
    """

    _instance: Optional[CircuitBreakerRegistry] = None
    _singleton_lock = threading.Lock()

    def __new__(cls) -> CircuitBreakerRegistry:
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._breakers = {}
                cls._instance._registry_lock = threading.RLock()
            return cls._instance

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        half_open_max_trials: int = 1,
    ) -> CircuitBreaker:
        """Récupère un disjoncteur existant ou le crée à la volée."""
        with self._registry_lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                    half_open_max_trials=half_open_max_trials,
                )
            return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Récupère un disjoncteur par son nom s'il existe."""
        with self._registry_lock:
            return self._breakers.get(name)

    def is_available(self, name: str) -> bool:
        """Vérifie si le service désigné peut exécuter une requête."""
        with self._registry_lock:
            breaker = self._breakers.get(name)
            if breaker is None:
                return True
            return breaker.can_execute()

    def get_status_summary(self) -> Dict[str, Dict[str, Any]]:
        """Génère un résumé complet de tous les disjoncteurs enregistrés."""
        with self._registry_lock:
            return {name: b.get_status() for name, b in self._breakers.items()}

    def reset_all(self) -> None:
        """Réinitialise tous les disjoncteurs."""
        with self._registry_lock:
            for b in self._breakers.values():
                b.reset()


# Instance globale partagée
circuit_breakers = CircuitBreakerRegistry()
