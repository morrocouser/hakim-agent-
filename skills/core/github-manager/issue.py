import subprocess
import json


def issue(action: str, params: dict = None) -> dict:
    """Manage issues"""
    params = params or {}

    if action == "create":
        return _create_issue(params)
    elif action == "list":
        return _list_issues(params)
    elif action == "close":
        return _close_issue(params)
    else:
        return {"error": f"Unknown action: {action}"}


def _create_issue(params: dict) -> dict:
    """Create an issue"""
    title = params.get("title", "New issue")
    body = params.get("body", "")
    labels = params.get("labels", [])

    try:
        cmd = ["gh", "issue", "create", "--title", title, "--body", body]
        if labels:
            cmd.extend(["--label", ",".join(labels)])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return {"success": True, "output": result.stdout.strip()}
        else:
            return {"error": result.stderr}
    except FileNotFoundError:
        return {"error": "gh CLI not installed"}
    except Exception as e:
        return {"error": str(e)}


def _list_issues(params: dict) -> dict:
    """List issues"""
    state = params.get("state", "open")

    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--state", state, "--json", "number,title,state"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            issues = json.loads(result.stdout) if result.stdout.strip() else []
            return {"issues": issues, "count": len(issues)}
        else:
            return {"error": result.stderr}
    except FileNotFoundError:
        return {"error": "gh CLI not installed"}
    except Exception as e:
        return {"error": str(e)}


def _close_issue(params: dict) -> dict:
    """Close an issue"""
    issue_number = params.get("number")

    if not issue_number:
        return {"error": "Issue number is required"}

    try:
        result = subprocess.run(
            ["gh", "issue", "close", str(issue_number)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"success": True, "issue_number": issue_number}
        else:
            return {"error": result.stderr}
    except FileNotFoundError:
        return {"error": "gh CLI not installed"}
    except Exception as e:
        return {"error": str(e)}
