"""Debug script for env propagation."""
import os
import subprocess
import sys

env = {k: v for k, v in os.environ.items() if k != "AXIOM_JWT_SECRET"}
env["AXIOM_JWT_SECRET"] = ""
print(f"Test env has key: {'AXIOM_JWT_SECRET' in env}, value: {env.get('AXIOM_JWT_SECRET')!r}")

# Child should see empty string
result = subprocess.run(
    [sys.executable, "-c", "import os; print('child sees:', repr(os.environ.get('AXIOM_JWT_SECRET', '<absent>')))"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    env=env,
    capture_output=True,
    text=True,
)
print(f"returncode: {result.returncode}")
print(f"stdout: {result.stdout}")
print(f"stderr: {result.stderr}")
