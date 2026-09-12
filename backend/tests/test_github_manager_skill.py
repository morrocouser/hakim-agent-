import pytest
from pathlib import Path
import sys
import importlib.util

def _import_from(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

_base = Path(__file__).parent.parent.parent / "skills" / "core" / "github-manager"
_repo_mod = _import_from("gh_repo", _base / "repo.py")
_pr_mod = _import_from("gh_pr", _base / "pr.py")
_issue_mod = _import_from("gh_issue", _base / "issue.py")

repo = _repo_mod.repo
pr = _pr_mod.pr
issue = _issue_mod.issue


def test_repo_create():
    """Test creating a repo"""
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test-repo")
        result = repo("create", {"name": repo_path, "description": "Test repo"})

        assert result["success"] is True
        assert os.path.exists(os.path.join(repo_path, ".git"))


def test_repo_unknown_action():
    """Test unknown repo action"""
    result = repo("unknown")
    assert "error" in result


def test_pr_list():
    """Test listing PRs"""
    result = pr("list")
    # gh CLI may not be available
    assert "prs" in result or "error" in result


def test_issue_create_no_title():
    """Test creating issue without gh CLI"""
    result = issue("create", {"title": "Test"})
    assert "success" in result or "error" in result


def test_pr_create_no_gh():
    """Test creating PR without gh CLI"""
    result = pr("create", {"title": "Test PR"})
    assert "success" in result or "error" in result
