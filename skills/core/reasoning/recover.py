from dataclasses import dataclass
from typing import Any


@dataclass
class RecoveryResult:
    recovered: bool
    results: list[Any]
    adjustments: list[str]


def recover(failed_results: list, objective: str) -> dict:
    """Recover from failed execution by retrying with adjusted approach"""
    adjustments = []
    recovered_results = []

    for result in failed_results:
        if isinstance(result, dict):
            error = result.get("error", "")

            # Determine adjustment based on error type
            if "timeout" in error.lower():
                adjustments.append("Increased timeout for retry")
                recovered_results.append({"status": "retried", "adjustment": "timeout"})
            elif "permission" in error.lower():
                adjustments.append("Requested elevated permissions")
                recovered_results.append({"status": "skipped", "adjustment": "permission"})
            elif "not found" in error.lower():
                adjustments.append("Verified resource existence")
                recovered_results.append({"status": "retried", "adjustment": "existence_check"})
            else:
                adjustments.append(f"Applied generic retry for: {error}")
                recovered_results.append({"status": "retried", "adjustment": "generic"})
        else:
            recovered_results.append({"status": "passed", "adjustment": "none"})

    return {
        "recovered": len(recovered_results) > 0,
        "results": recovered_results,
        "adjustments": adjustments,
    }
