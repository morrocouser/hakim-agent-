"""Policy Gateway & Action Boundary (OpenBot Fail-Closed Architecture).

Every action performed by a coworker (bot), routine, or human
passes through this fail-closed governance gateway before execution.
It evaluates tools, intents, initiator kinds (person vs routine vs handoff),
and targets against explicit security rules.
"""

from __future__ import annotations
import os
import re
import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from axiom.logging_setup import log


class PolicyDecision(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REQUIRE_TAKEOVER = "REQUIRE_TAKEOVER"  # "Take the Wheel" required by a human


class InitiatorKind(str, Enum):
    PERSON = "person"                  # Human user watching/typing in room
    ROUTINE = "routine"                # Scheduled autonomous background task
    RESPONSIBILITY = "responsibility"  # Bot standing autonomous duty
    HANDOFF = "handoff"                # Another bot delegated this subtask
    DEPLOYMENT = "deployment"          # System startup / health boundary


class ActionRequest(BaseModel):
    tool_name: str
    intent: str
    coworker_id: str
    coworker_name: Optional[str] = None
    actor_id: str = "default_user"
    initiator_kind: InitiatorKind = InitiatorKind.PERSON
    initiator_id: Optional[str] = None
    target: Optional[str] = None
    command: Optional[str] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    decision: PolicyDecision
    rule_id: str
    reason: str
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    action_request: ActionRequest
    evaluated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Sensitive patterns requiring "Take the Wheel" or human confirmation
SENSITIVE_URL_PATTERNS = [
    r"login|signin|connexion|auth|oauth|sso",
    r"2fa|mfa|otp|verify|authenticator",
    r"captcha|recaptcha|hcaptcha|challenge",
    r"checkout|billing|payment|stripe|paypal|bank",
    r"password|reset|security|account/delete",
]

# Destructive shell command patterns
DESTRUCTIVE_COMMAND_PATTERNS = [
    r"\brm\s+-(?:r|f|rf|fr)\s+[/~]",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r"\bformat\s+[a-z]:",
    r"\bshutdown\b",
    r"\breboot\b",
    r":\(\)\{ :\|:& \};:",  # Fork bomb
    r"\bchmod\s+-R\s+777\s+/",
    r"\bcurl.*\|\s*(?:bash|sh|powershell)",
]


class PolicyGateway:
    """Fail-Closed Governance Gateway inspired by CopilotKit OpenBot."""

    def __init__(self):
        self._custom_rules: List[Dict[str, Any]] = []

    def evaluate(self, req: ActionRequest) -> EvaluationResult:
        """Evaluate an action against security & governance policies.
        
        Evaluates in order:
        1. Critical destructive commands -> DENIED
        2. Sensitive human intervention triggers (2FA/Auth/Payment) -> REQUIRE_TAKEOVER
        3. Nobody watching policy (unattended routine or handoff attempting high-risk tool) -> DENIED or REQUIRE_TAKEOVER
        4. Standard tools -> ALLOWED
        """
        is_unattended = req.initiator_kind in (
            InitiatorKind.ROUTINE,
            InitiatorKind.RESPONSIBILITY,
            InitiatorKind.HANDOFF,
        )

        cmd = req.command or req.parameters.get("command", "") or ""
        url = req.url or req.parameters.get("url", "") or ""
        path = req.file_path or req.parameters.get("path", "") or ""

        # 1. Check Destructive Shell Commands
        if req.tool_name in ("execute_code", "shell_exec", "terminal"):
            for pattern in DESTRUCTIVE_COMMAND_PATTERNS:
                if re.search(pattern, cmd, re.IGNORECASE):
                    return EvaluationResult(
                        decision=PolicyDecision.DENIED,
                        rule_id="RULE_DESTRUCTIVE_COMMAND_BLOCKED",
                        reason=f"Commande destructive bloquée par la politique de sécurité : '{pattern}'",
                        risk_level="CRITICAL",
                        action_request=req,
                    )

        # 2. Check Browser Navigation to Sensitive Checkpoints (Take the Wheel)
        if req.tool_name in ("browser_navigate", "web_browse", "browser_click", "browser"):
            for pattern in SENSITIVE_URL_PATTERNS:
                if re.search(pattern, url, re.IGNORECASE) or re.search(pattern, req.intent, re.IGNORECASE):
                    return EvaluationResult(
                        decision=PolicyDecision.REQUIRE_TAKEOVER,
                        rule_id="RULE_HUMAN_TAKEOVER_SENSITIVE_SURFACE",
                        reason=f"Point de contrôle sensible détecté ({pattern}). Prise de contrôle humaine ('Take the Wheel') nécessaire.",
                        risk_level="HIGH",
                        action_request=req,
                    )

        # 3. Unattended High-Risk Guardrail (Nobody Watching)
        if is_unattended:
            # Unattended destructive file deletion or system modification is strictly denied
            if req.tool_name in ("delete_file", "write_system_file") or (req.tool_name == "shell_exec" and "rm" in cmd):
                return EvaluationResult(
                    decision=PolicyDecision.DENIED,
                    rule_id="RULE_UNATTENDED_RISKY_OPERATION_DENIED",
                    reason="Opération à haut risque refusée en mode autonome ('Nobody watching'). Un opérateur humain doit être présent.",
                    risk_level="HIGH",
                    action_request=req,
                )

        # 4. Critical File Paths Outside Workspace
        if req.tool_name in ("create_file", "edit_file", "delete_file", "file_manager"):
            clean_path = path.replace("\\", "/").lower()
            if any(forbidden in clean_path for forbidden in ["/windows/", "/system32/", "/etc/", "/var/", "c:/windows"]):
                return EvaluationResult(
                    decision=PolicyDecision.DENIED,
                    rule_id="RULE_SYSTEM_PATH_RESTRICTION",
                    reason="Accès interdit aux répertoires critiques du système d'exploitation.",
                    risk_level="CRITICAL",
                    action_request=req,
                )

        # 5. Default Allow for safe governed operations
        return EvaluationResult(
            decision=PolicyDecision.ALLOWED,
            rule_id="RULE_DEFAULT_GOVERNED_ALLOW",
            reason="Action validée et conforme aux règles de gouvernance du coworker.",
            risk_level="LOW",
            action_request=req,
        )


# Global singleton
policy_gateway = PolicyGateway()
