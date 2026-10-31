"""
AXIOM v4.0 — Observabilité et Traçage Standardisé OpenInference / OpenTelemetry.

Fournit une infrastructure de traçage hiérarchique suivant les conventions sémantiques
OpenInference (AGENT, CHAIN, LLM, TOOL, EVAL). Compatible avec OpenTelemetry,
Langfuse, Arize Phoenix, ou en mode autonome ultra-léger avec export JSONLines.
"""

from __future__ import annotations

import time
import json
import uuid
import os
from enum import Enum
from pathlib import Path
from contextvars import ContextVar
from typing import Optional, Dict, Any, List
from axiom.logging_setup import log


# =============================================================================
# CONVENTIONS SÉMANTIQUES OPENINFERENCE
# =============================================================================

class SpanKind(str, Enum):
    AGENT = "AGENT"      # Exécution globale d'un agent autonome
    CHAIN = "CHAIN"      # Étape ou chaîne de raisonnement (ex: itération ReAct)
    LLM = "LLM"          # Inférence auprès d'un grand modèle de langage
    TOOL = "TOOL"        # Exécution d'un outil externe (recherche, fichiers, bash)
    EVAL = "EVAL"        # Évaluation / Auto-critique de qualité
    RETRIEVER = "RETRIEVER"  # Recherche vectorielle ou documentaire


class SpanAttributes:
    OPENINFERENCE_SPAN_KIND = "openinference.span.kind"
    INPUT_VALUE = "input.value"
    OUTPUT_VALUE = "output.value"
    INPUT_MIME_TYPE = "input.mime_type"
    OUTPUT_MIME_TYPE = "output.mime_type"
    
    # Attributs LLM
    LLM_MODEL_NAME = "llm.model_name"
    LLM_INVOCATION_PARAMETERS = "llm.invocation_parameters"
    LLM_TOKEN_COUNT_PROMPT = "llm.token_count.prompt"
    LLM_TOKEN_COUNT_COMPLETION = "llm.token_count.completion"
    LLM_TOKEN_COUNT_TOTAL = "llm.token_count.total"
    
    # Attributs Tool
    TOOL_NAME = "tool.name"
    TOOL_PARAMETERS = "tool.parameters"
    
    # Métadonnées d'exécution
    SESSION_ID = "session.id"
    USER_ID = "user.id"
    ERROR_TYPE = "error.type"
    ERROR_MESSAGE = "error.message"


# =============================================================================
# MODÈLE DE SPAN ET GESTIONNAIRE DE CONTEXTE
# =============================================================================

class Span:
    """Représente une unité d'exécution hiérarchique (span de traçage)."""

    def __init__(
        self,
        name: str,
        kind: SpanKind,
        trace_id: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        tracer: Optional[TelemetryTracer] = None,
    ):
        self.name = name
        self.kind = kind
        self.trace_id = trace_id
        self.span_id = f"span_{uuid.uuid4().hex[:12]}"
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: kind.value,
        }
        if attributes:
            self.attributes.update(attributes)
        self.status = "OK"
        self.error_message: Optional[str] = None
        self._tracer = tracer
        self._token = None

    def set_attribute(self, key: str, value: Any) -> Span:
        """Enregistre un attribut sémantique sur le span."""
        if value is not None:
            self.attributes[key] = value
        return self

    def set_attributes(self, attrs: Dict[str, Any]) -> Span:
        """Enregistre plusieurs attributs en une seule fois."""
        for k, v in attrs.items():
            self.set_attribute(k, v)
        return self

    def set_status(self, status: str, error_message: Optional[str] = None) -> Span:
        """Définit le statut final du span (OK ou ERROR)."""
        self.status = status
        if error_message:
            self.error_message = error_message
            self.attributes[SpanAttributes.ERROR_MESSAGE] = error_message
        return self

    def end(self) -> None:
        """Clôture le span et calcule sa durée."""
        if self.end_time is None:
            self.end_time = time.time()
            if self._tracer:
                self._tracer._on_span_ended(self)

    @property
    def duration_ms(self) -> float:
        """Durée d'exécution du span en millisecondes."""
        if self.end_time is None:
            return round((time.time() - self.start_time) * 1000, 2)
        return round((self.end_time - self.start_time) * 1000, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le span en dictionnaire JSON-compatible."""
        return {
            "name": self.name,
            "kind": self.kind.value,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error_message": self.error_message,
            "attributes": self.attributes,
        }

    def __enter__(self) -> Span:
        if self._tracer:
            self._token = self._tracer._push_span(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.set_status("ERROR", str(exc_val))
            self.attributes[SpanAttributes.ERROR_TYPE] = exc_type.__name__
        self.end()
        if self._tracer and self._token:
            self._tracer._pop_span(self._token)


# =============================================================================
# MOTEUR DE TÉLÉMÉTRIE (TRACER)
# =============================================================================

_CURRENT_SPAN: ContextVar[Optional[Span]] = ContextVar("axiom_current_span", default=None)


class TelemetryTracer:
    """
    Gestionnaire central des traces et spans pour AXIOM.
    Gère la corrélation parent-enfant et l'export structuré.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else Path(os.getenv("AXIOM_TRACE_FILE", Path.home() / ".axiom" / "traces.jsonl"))
        )
        self.enabled = os.getenv("AXIOM_TRACING", "1") == "1"
        self._recent_traces: List[Dict[str, Any]] = []
        self._max_recent = 50

    def _push_span(self, span: Span) -> Any:
        return _CURRENT_SPAN.set(span)

    def _pop_span(self, token: Any) -> None:
        _CURRENT_SPAN.reset(token)

    def get_current_span(self) -> Optional[Span]:
        """Retourne le span actif dans le contexte asynchrone courant."""
        return _CURRENT_SPAN.get()

    def get_current_trace_id(self) -> Optional[str]:
        """Retourne l'identifiant de trace courant s'il existe."""
        span = self.get_current_span()
        return span.trace_id if span else None

    def start_as_current_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.CHAIN,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """
        Démarre un nouveau span enfant du span courant, ou un nouveau root span.
        """
        parent = self.get_current_span()
        if parent:
            trace_id = parent.trace_id
            parent_id = parent.span_id
        else:
            trace_id = f"trace_{uuid.uuid4().hex[:16]}"
            parent_id = None

        return Span(
            name=name,
            kind=kind,
            trace_id=trace_id,
            parent_span_id=parent_id,
            attributes=attributes,
            tracer=self,
        )

    def _on_span_ended(self, span: Span) -> None:
        """Enregistre le span lors de sa finalisation."""
        if not self.enabled:
            return

        span_dict = span.to_dict()
        self._recent_traces.append(span_dict)
        if len(self._recent_traces) > self._max_recent:
            self._recent_traces.pop(0)

        # Si c'est un span racine (sans parent), écrire dans le fichier JSONLines
        if span.parent_span_id is None:
            self._export_to_file(span_dict)

    def _export_to_file(self, data: Dict[str, Any]) -> None:
        """Écrit la trace terminée sur disque."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception as e:
            log.debug("Impossible d'écrire la trace sur disque: %s", e)

    def get_recent_traces(self) -> List[Dict[str, Any]]:
        """Retourne les dernières traces enregistrées en mémoire."""
        return list(self._recent_traces)

    def clear(self) -> None:
        """Vide l'historique des traces en mémoire."""
        self._recent_traces.clear()


# Instance globale partagée
tracer = TelemetryTracer()
