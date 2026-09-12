import subprocess


def background(command: str, cwd: str = None) -> dict:
    """Run a command in background"""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
        )

        return {
            "pid": process.pid,
            "status": "started",
            "command": command,
        }
    except Exception as e:
        return {
            "pid": None,
            "status": "failed",
            "error": str(e),
        }
