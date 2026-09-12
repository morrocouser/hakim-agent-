import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class TestResult:
    passed: bool
    total: int
    passed_count: int
    failed_count: int
    errors: list[str]
    duration: float


def run_tests(test_path: str = None) -> dict:
    """Run tests and return results"""
    try:
        cmd = ["python", "-m", "pytest", test_path or ".", "-v", "--tb=short"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = result.stdout
        passed = result.returncode == 0

        passed_count = output.count("PASSED")
        failed_count = output.count("FAILED")
        total = passed_count + failed_count

        errors = []
        if not passed:
            for line in output.split("\n"):
                if "FAILED" in line:
                    errors.append(line.strip())

        return {
            "passed": passed,
            "total": total,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "errors": errors,
            "duration": 0.0,
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": False, "total": 0, "passed_count": 0,
            "failed_count": 0, "errors": ["Test execution timed out"], "duration": 60.0,
        }
    except Exception as e:
        return {
            "passed": False, "total": 0, "passed_count": 0,
            "failed_count": 0, "errors": [str(e)], "duration": 0.0,
        }
