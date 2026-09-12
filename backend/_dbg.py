"""Quick env propagation debug."""
import os, subprocess, sys
env = {k: v for k, v in os.environ.items() if k != "AXIOM_JWT_SECRET"}
print(f"filtered env has AXIOM_JWT_SECRET key? {'AXIOM_JWT_SECRET' in env}")
proc = subprocess.run(
    [sys.executable, "-c", "import os; print('child secret:', repr(os.environ.get('AXIOM_JWT_SECRET', '<absent>')))"],
    env=env, capture_output=True, text=True, cwd=".",
)
print("rc:", proc.returncode)
print("stdout:", proc.stdout)
print("stderr:", proc.stderr)
