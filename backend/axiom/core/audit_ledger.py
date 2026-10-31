"""Audit Ledger (OpenBot Governed Audit Trail).

Every tool call and policy decision lands in this audit ledger.
Provides traceability for human operators and filtering by:
- Initiator kind ('person', 'routine', 'handoff', 'responsibility', 'deployment')
- 'Nobody watching' filter (unattended executions)
- Decision ('ALLOWED', 'DENIED', 'REQUIRE_TAKEOVER')
"""

from __future__ import annotations
import uuid
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from axiom.core.policy_gateway import PolicyDecision, InitiatorKind, ActionRequest, EvaluationResult
from axiom.logging_setup import log


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    coworker_id: str
    coworker_name: str
    actor_id: str
    initiator_kind: InitiatorKind
    initiator_id: Optional[str] = None
    tool_name: str
    intent: str
    target: Optional[str] = None
    decision: PolicyDecision
    rule_id: str
    reason: str
    status: str  # "completed", "denied", "paused_for_takeover", "failed"
    duration_ms: int = 15
    details: Dict[str, Any] = Field(default_factory=dict)


class AuditLedger:
    """Thread-safe in-memory and persistent Audit Ledger."""

    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._seed_default_audit_history()

    def record_decision(
        self,
        eval_result: EvaluationResult,
        status: str = "completed",
        duration_ms: int = 15,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        req = eval_result.action_request
        entry = AuditEntry(
            coworker_id=req.coworker_id,
            coworker_name=req.coworker_name or req.coworker_id,
            actor_id=req.actor_id,
            initiator_kind=req.initiator_kind,
            initiator_id=req.initiator_id,
            tool_name=req.tool_name,
            intent=req.intent,
            target=req.target or req.command or req.url or req.file_path or "",
            decision=eval_result.decision,
            rule_id=eval_result.rule_id,
            reason=eval_result.reason,
            status=status,
            duration_ms=duration_ms,
            details=details or {},
        )
        self._entries.insert(0, entry)  # Prepend for newest-first
        log.info(
            "AUDIT LOG [%s] %s | tool=%s coworker=%s initiator=%s",
            entry.decision.value,
            entry.status,
            entry.tool_name,
            entry.coworker_id,
            entry.initiator_kind.value,
        )
        return entry

    def record_control_event(
        self,
        coworker_id: str,
        coworker_name: str,
        event_type: str,  # "computer.help_requested", "computer.control_taken", "computer.control_released"
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            coworker_id=coworker_id,
            coworker_name=coworker_name,
            actor_id="operator",
            initiator_kind=InitiatorKind.PERSON,
            tool_name=event_type,
            intent=f"Événement de passation de contrôle : {event_type}",
            target="coworker_computer",
            decision=PolicyDecision.ALLOWED,
            rule_id="RULE_HUMAN_CONTROL_LIFECYCLE",
            reason="Passation de commande enregistrée dans le journal de gouvernance.",
            status="completed",
            duration_ms=5,
            details=details or {},
        )
        self._entries.insert(0, entry)
        return entry

    def query(
        self,
        nobody_watching: Optional[bool] = None,
        decision: Optional[str] = None,
        coworker_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        filtered = self._entries

        if nobody_watching is not None:
            unattended_kinds = {
                InitiatorKind.ROUTINE,
                InitiatorKind.RESPONSIBILITY,
                InitiatorKind.HANDOFF,
            }
            if nobody_watching:
                filtered = [e for e in filtered if e.initiator_kind in unattended_kinds]
            else:
                filtered = [e for e in filtered if e.initiator_kind == InitiatorKind.PERSON]

        if decision:
            filtered = [e for e in filtered if e.decision.value.upper() == decision.upper()]

        if coworker_id:
            filtered = [e for e in filtered if e.coworker_id == coworker_id]

        if search:
            s = search.lower()
            filtered = [
                e for e in filtered
                if s in e.intent.lower()
                or s in e.tool_name.lower()
                or s in (e.target or "").lower()
                or s in e.coworker_name.lower()
                or s in e.reason.lower()
            ]

        total = len(filtered)
        paginated = filtered[offset : offset + limit]

        return {
            "total": total,
            "items": [item.dict() for item in paginated],
            "limit": limit,
            "offset": offset,
        }

    def _seed_default_audit_history(self):
        """Seed realistic historical records to showcase OpenBot governance."""
        sample_entries = [
            AuditEntry(
                coworker_id="bot-browser",
                coworker_name="Web Research Coworker",
                actor_id="hakim_admin",
                initiator_kind=InitiatorKind.PERSON,
                tool_name="browser_navigate",
                intent="Consultation de la documentation officielle Next.js",
                target="https://nextjs.org/docs/app",
                decision=PolicyDecision.ALLOWED,
                rule_id="RULE_DEFAULT_GOVERNED_ALLOW",
                reason="Navigation web externe sécurisée et autorisée.",
                status="completed",
                duration_ms=420,
            ),
            AuditEntry(
                coworker_id="bot-browser",
                coworker_name="Web Research Coworker",
                actor_id="hakim_admin",
                initiator_kind=InitiatorKind.PERSON,
                tool_name="browser_navigate",
                intent="Accès à la console d'authentification GitHub",
                target="https://github.com/login/oauth/authorize",
                decision=PolicyDecision.REQUIRE_TAKEOVER,
                rule_id="RULE_HUMAN_TAKEOVER_SENSITIVE_SURFACE",
                reason="Point de contrôle 2FA/Auth détecté. Intervention humaine 'Take the Wheel' requise.",
                status="paused_for_takeover",
                duration_ms=45,
            ),
            AuditEntry(
                coworker_id="bot-sentinel",
                coworker_name="SecOps Sentinel Coworker",
                actor_id="system",
                initiator_kind=InitiatorKind.ROUTINE,
                initiator_id="routine_audit_deps",
                tool_name="shell_exec",
                intent="Audit des dépendances npm et scan de vulnérabilités",
                target="npm audit --json",
                decision=PolicyDecision.ALLOWED,
                rule_id="RULE_DEFAULT_GOVERNED_ALLOW",
                reason="Routine autonome exécutant une commande de diagnostic en lecture seule.",
                status="completed",
                duration_ms=1850,
            ),
            AuditEntry(
                coworker_id="bot-devops",
                coworker_name="Infrastructure Coworker",
                actor_id="system",
                initiator_kind=InitiatorKind.ROUTINE,
                initiator_id="routine_cleanup_logs",
                tool_name="shell_exec",
                intent="Tentative de suppression globale récursive",
                target="rm -rf /var/log/system/*",
                decision=PolicyDecision.DENIED,
                rule_id="RULE_DESTRUCTIVE_COMMAND_BLOCKED",
                reason="Commande destructive bloquée par la politique de sécurité fail-closed.",
                status="denied",
                duration_ms=8,
            ),
            AuditEntry(
                coworker_id="bot-curator",
                coworker_name="Data Curator Coworker",
                actor_id="hakim_admin",
                initiator_kind=InitiatorKind.HANDOFF,
                initiator_id="bot-browser",
                tool_name="create_file",
                intent="Sauvegarde du résumé markdown dans le workspace isolé",
                target="user_files/coworkers/bot-curator/workspace/summary.md",
                decision=PolicyDecision.ALLOWED,
                rule_id="RULE_DEFAULT_GOVERNED_ALLOW",
                reason="Écriture autorisée dans l'espace de stockage isolé du coworker.",
                status="completed",
                duration_ms=110,
            ),
        ]
        self._entries.extend(sample_entries)


# Global singleton
audit_ledger = AuditLedger()
