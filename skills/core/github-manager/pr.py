import subprocess


def pr(action: str, params: dict = None) -> dict:
    """Manage pull requests"""
    params = params or {}

    if action == "create":
        return _create_pr(params)
    elif action == "list":
        return _list_prs(params)
    elif action == "merge":
        return _merge_pr(params)
    else:
        return {"error": f"Unknown action: {action}"}


def _create_pr(params: dict) -> dict:
    """Create a pull request (via gh CLI)"""
    title = params.get("title", "Update")
    body = params.get("body", "")
    base = params.get("base", "main")
    head = params.get("head", "HEAD")

    try:
        result = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body, "--base", base, "--head", head],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"success": True, "output": result.stdout.strip()}
        else:
            return {"error": result.stderr}
    except FileNotFoundError:
        return {"error": "gh CLI not installed"}
    except Exception as e:
        return {"error": str(e)}


def _list_prs(params: dict) -> dict:
    """List pull requests"""
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--json", "number,title,state"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            import json
            prs = json.loads(result.stdout) if result.stdout.strip() else []
            return {"prs": prs, "count": len(prs)}
        else:
            return {"error": result.stderr}
    except FileNotFoundError:
        return {"error": "gh CLI not installed"}
    except Exception as e:
        return {"error": str(e)}


def _merge_pr(params: dict) -> dict:
    """Merge a pull request"""
    pr_number = params.get("number")

    if not pr_number:
        return {"error": "PR number is required"}

    try:
        result = subprocess.run(
            ["gh", "pr", "merge", str(pr_number), "--merge"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"success": True, "pr_number": pr_number}
        else:
            return {"error": result.stderr}
    except FileNotFoundError:
        return {"error": "gh CLI not installed"}
    except Exception as e:
        return {"error": str(e)}
