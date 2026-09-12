import subprocess
import os


def repo(action: str, params: dict = None) -> dict:
    """Manage repositories"""
    params = params or {}

    if action == "create":
        return _create_repo(params)
    elif action == "clone":
        return _clone_repo(params)
    elif action == "list":
        return _list_repos(params)
    else:
        return {"error": f"Unknown action: {action}"}


def _create_repo(params: dict) -> dict:
    """Create a new repository"""
    name = params.get("name", "new-repo")
    description = params.get("description", "")

    try:
        os.makedirs(name, exist_ok=True)
        subprocess.run(["git", "init"], cwd=name, capture_output=True)

        readme_content = f"# {name}\n\n{description}\n"
        with open(os.path.join(name, "README.md"), "w") as f:
            f.write(readme_content)

        subprocess.run(["git", "add", "."], cwd=name, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=name, capture_output=True)

        return {
            "success": True,
            "name": name,
            "path": os.path.abspath(name),
        }
    except Exception as e:
        return {"error": str(e)}


def _clone_repo(params: dict) -> dict:
    """Clone a repository"""
    url = params.get("url", "")
    destination = params.get("destination", ".")

    if not url:
        return {"error": "URL is required"}

    try:
        result = subprocess.run(
            ["git", "clone", url],
            cwd=destination,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"success": True, "url": url, "destination": destination}
        else:
            return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}


def _list_repos(params: dict) -> dict:
    """List git repos in a directory"""
    path = params.get("path", ".")

    try:
        repos = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, ".git")):
                repos.append({"name": item, "path": os.path.abspath(item_path)})

        return {"repos": repos, "count": len(repos)}
    except Exception as e:
        return {"error": str(e)}
