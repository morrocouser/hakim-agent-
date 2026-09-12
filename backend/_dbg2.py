"""Direct test of jwt.py behavior in subprocess without dotenv interference."""
import os, subprocess, sys

env = {k: v for k, v in os.environ.items() if k != "AXIOM_JWT_SECRET"}
print(f"Parent filtered env has key? {'AXIOM_JWT_SECRET' in env}")

# Run python in the backend dir, with a minimal -c that just imports jwt
proc = subprocess.run(
    [sys.executable, "-c",
     "import os, sys; "
     "sys.path.insert(0, '.'); "
     "print('child secret before import:', repr(os.environ.get('AXIOM_JWT_SECRET', '<absent>')), flush=True); "
     "try: "
     "  from axiom.auth import jwt; "
     "  print('jwt import OK, SECRET_KEY:', repr(jwt.SECRET_KEY)[:30], flush=True) "
     "except RuntimeError as e: "
     "  print('RuntimeError raised:', str(e), flush=True)"],
    cwd=".", env=env, capture_output=True, text=True
)
print(f"rc: {proc.returncode}")
print(f"stdout: {proc.stdout}")
print(f"stderr: {proc.stderr}")
