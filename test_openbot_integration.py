"""Test OpenBot integration: Policy Gateway, Audit Ledger, Coworker Virtual Computer, and Routes."""

import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from axiom.core.policy_gateway import (
    policy_gateway, PolicyDecision, InitiatorKind, ActionRequest
)
from axiom.core.audit_ledger import audit_ledger
from axiom.core.coworker_computer import coworker_manager, ControlState


def test_policy_gateway_rules():
    # 1. Test destructive command -> DENIED
    req_destructive = ActionRequest(
        tool_name="shell_exec",
        intent="Delete all files",
        coworker_id="bot-devops",
        command="rm -rf /",
        initiator_kind=InitiatorKind.PERSON,
    )
    eval_destr = policy_gateway.evaluate(req_destructive)
    assert eval_destr.decision == PolicyDecision.DENIED
    assert "destructive" in eval_destr.reason.lower()

    # 2. Test sensitive URL -> REQUIRE_TAKEOVER ("Take the Wheel")
    req_takeover = ActionRequest(
        tool_name="browser_navigate",
        intent="Connexion compte GitHub avec 2FA",
        coworker_id="bot-browser",
        url="https://github.com/login/oauth/authorize",
        initiator_kind=InitiatorKind.PERSON,
    )
    eval_takeover = policy_gateway.evaluate(req_takeover)
    assert eval_takeover.decision == PolicyDecision.REQUIRE_TAKEOVER
    assert "take the wheel" in eval_takeover.reason.lower() or "intervention" in eval_takeover.reason.lower()

    # 3. Test safe governed command -> ALLOWED
    req_safe = ActionRequest(
        tool_name="shell_exec",
        intent="Vérification des versions",
        coworker_id="bot-devops",
        command="npm --version",
        initiator_kind=InitiatorKind.PERSON,
    )
    eval_safe = policy_gateway.evaluate(req_safe)
    assert eval_safe.decision == PolicyDecision.ALLOWED


def test_coworker_take_the_wheel_handover():
    coworker_id = "bot-browser"
    
    # 1. Simulate coworker requesting help (e.g. captcha)
    coworker_manager.request_help(coworker_id, "CAPTCHA détecté sur la mire de connexion")
    c = coworker_manager.get_coworker(coworker_id)
    assert c.control_state == ControlState.HELP_REQUESTED
    assert "CAPTCHA" in c.help_reason

    # 2. Operator takes the wheel
    coworker_manager.take_the_wheel(coworker_id, "Hakim Operator")
    c = coworker_manager.get_coworker(coworker_id)
    assert c.control_state == ControlState.HUMAN_CONTROLLED

    # 3. Operator releases the wheel
    coworker_manager.release_the_wheel(coworker_id, "Hakim Operator")
    c = coworker_manager.get_coworker(coworker_id)
    assert c.control_state == ControlState.BOT_ACTIVE


def test_audit_ledger_nobody_watching():
    # Query with nobody_watching filter
    result = audit_ledger.query(nobody_watching=True)
    assert "items" in result
    for item in result["items"]:
        assert item["initiator_kind"] in ("routine", "handoff", "responsibility", "memory")

    # Query with decision filter
    denied = audit_ledger.query(decision="DENIED")
    for item in denied["items"]:
        assert item["decision"] == "DENIED"


if __name__ == "__main__":
    test_policy_gateway_rules()
    test_coworker_take_the_wheel_handover()
    test_audit_ledger_nobody_watching()
    print("ALL OPENBOT INTEGRATION TESTS PASSED SUCCESSFULLY!")
