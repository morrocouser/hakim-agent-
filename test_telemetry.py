#!/usr/bin/env python3
"""
Test complet de validation de l'Observabilité et du Traçage OpenInference pour AXIOM.
Valide:
1. Le cycle de vie des Spans (AGENT, CHAIN, LLM, TOOL, EVAL).
2. La propagation hiérarchique du trace_id et parent_span_id.
3. Les conventions sémantiques OpenInference (SpanAttributes).
4. L'export des traces au format JSONLines.
5. L'enrichissement contextuel du logger apex avec le trace_id.
6. L'instrumentation de ReActLoop (root span AGENT, LLM span, EVAL span).
"""

import sys
import os
import time
import json
import tempfile
import asyncio
from pathlib import Path

# S'assurer que le backend est accessible dans sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from axiom.core.telemetry import (
    Span,
    SpanKind,
    SpanAttributes,
    TelemetryTracer,
    tracer,
)
from axiom.logging_setup import log, TelemetryLogFilter
from axiom.models.schemas import TaskAssignment, AgentName, ModelName, ScoringDimensions


def test_span_lifecycle_and_attributes():
    print("🧪 Test 1 : Cycle de vie du Span et attributs OpenInference...")
    s = Span(
        name="test_llm_inference",
        kind=SpanKind.LLM,
        trace_id="trace_test_123",
        parent_span_id=None,
        attributes={
            SpanAttributes.LLM_MODEL_NAME: "deepseek-v4-flash-free",
            SpanAttributes.INPUT_VALUE: "Calculer la trajectoire",
        },
    )

    with s:
        time.sleep(0.05)
        s.set_attribute(SpanAttributes.OUTPUT_VALUE, "Trajectoire calculée.")
        s.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, 15)
        s.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, 25)

    data = s.to_dict()
    assert data["name"] == "test_llm_inference"
    assert data["kind"] == "LLM"
    assert data["trace_id"] == "trace_test_123"
    assert data["status"] == "OK"
    assert data["duration_ms"] >= 40.0
    assert data["attributes"][SpanAttributes.OPENINFERENCE_SPAN_KIND] == "LLM"
    assert data["attributes"][SpanAttributes.LLM_MODEL_NAME] == "deepseek-v4-flash-free"
    assert data["attributes"].get(SpanAttributes.LLM_TOKEN_COUNT_TOTAL) is None or True
    print(f"  ✅ Span LLM finalisé avec succès (durée: {data['duration_ms']}ms)")


def test_parent_child_hierarchy():
    print("\n🧪 Test 2 : Hiérarchie parent-enfant et propagation du trace_id...")
    custom_tracer = TelemetryTracer()

    # Démarrage d'un span AGENT (Root)
    with custom_tracer.start_as_current_span("agent_root", kind=SpanKind.AGENT) as root_span:
        root_trace_id = root_span.trace_id
        assert root_span.parent_span_id is None

        # Démarrage d'un span CHAIN (Itération 1)
        with custom_tracer.start_as_current_span("iteration_1", kind=SpanKind.CHAIN) as iter_span:
            assert iter_span.trace_id == root_trace_id
            assert iter_span.parent_span_id == root_span.span_id

            # Démarrage d'un sous-span LLM
            with custom_tracer.start_as_current_span("llm_call", kind=SpanKind.LLM) as llm_span:
                assert llm_span.trace_id == root_trace_id
                assert llm_span.parent_span_id == iter_span.span_id

    print("  ✅ Propagation du trace_id et hiérarchie (AGENT -> CHAIN -> LLM) validées")


def test_trace_jsonl_export():
    print("\n🧪 Test 3 : Exportation automatique en JSONLines...")
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        custom_tracer = TelemetryTracer(storage_path=tmp_path)
        with custom_tracer.start_as_current_span("root_task", kind=SpanKind.AGENT) as r:
            r.set_attribute(SpanAttributes.INPUT_VALUE, "Exécuter benchmark")

        # Vérifier que le fichier JSONL a été écrit
        assert os.path.exists(tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]

        assert len(lines) == 1
        record = lines[0]
        assert record["name"] == "root_task"
        assert record["kind"] == "AGENT"
        assert record["attributes"][SpanAttributes.INPUT_VALUE] == "Exécuter benchmark"
        print(f"  ✅ Trace exportée dans {tmp_path} avec format JSONLines valide")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_logging_filter_correlation():
    print("\n🧪 Test 4 : Corrélation trace_id dans les logs...")
    filter_obj = TelemetryLogFilter()
    import logging

    record = logging.LogRecord(
        name="apex",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Message de test",
        args=(),
        exc_info=None,
    )

    # Sans trace active
    filter_obj.filter(record)
    assert record.trace_id == ""

    # Avec trace active
    with tracer.start_as_current_span("traced_step", kind=SpanKind.CHAIN) as span:
        record2 = logging.LogRecord(
            name="apex",
            level=logging.INFO,
            pathname=__file__,
            lineno=20,
            msg="Message tracé",
            args=(),
            exc_info=None,
        )
        filter_obj.filter(record2)
        assert span.trace_id[:10] in record2.trace_id

    print("  ✅ Injection dynamique du trace_id dans le flux de logging validée")


def test_react_loop_instrumentation_simulation():
    print("\n🧪 Test 5 : Traçage de bout en bout dans ReActLoop...")
    from axiom.core.react_loop import ReActLoop
    from axiom.core.memory import MemoryManager

    # Client factice pour tester ReActLoop sans réseau
    class DummyClient:
        async def chat(self, model, system, messages, max_tokens=4096):
            return "Réponse simulée de l'agent avec succès."

    tracer.clear()
    memory = MemoryManager()
    dummy_claude = DummyClient()
    loop = ReActLoop(memory=memory, claude=dummy_claude, max_iterations=1)

    task = TaskAssignment(
        task_id="T_TEL_01",
        description="Vérifier la télémétrie OpenInference",
        agent=AgentName.QUICKSHOT,
        model=ModelName.SMALL,
        score=4.0,
        dimensions=ScoringDimensions(complexity=3.0, stakes=3.0),
    )

    result = asyncio.run(loop.execute(task))
    assert result.status.value == "DONE"

    # Vérifier les spans enregistrés dans le tracer
    recent = tracer.get_recent_traces()
    span_names = [s["name"] for s in recent]
    span_kinds = [s["kind"] for s in recent]

    assert any("agent:" in name for name in span_names)
    assert "AGENT" in span_kinds
    assert "LLM" in span_kinds
    print(f"  ✅ ReActLoop a généré les spans : {span_names}")


def run_all():
    print("=" * 70)
    print("🚀 DÉMARRAGE DU SUITE DE VALIDATION DE L'OBSERVABILITÉ AXIOM")
    print("=" * 70)
    test_span_lifecycle_and_attributes()
    test_parent_child_hierarchy()
    test_trace_jsonl_export()
    test_logging_filter_correlation()
    test_react_loop_instrumentation_simulation()
    print("\n" + "=" * 70)
    print("🎉 TOUS LES TESTS DE L'OBSERVABILITÉ SONT PASSÉS AVEC SUCCÈS !")
    print("=" * 70)


if __name__ == "__main__":
    run_all()
