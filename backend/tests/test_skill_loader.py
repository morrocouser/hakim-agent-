"""Tests for SkillLoader. Run: .venv\Scripts\python.exe -m pytest backend/tests/test_skill_loader.py -v"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # backend/

from axiom.skills.loader import load_skill, SkillManifest


def test_load_skill_from_directory(tmp_path):
    """Test loading a skill from a directory with SKILL.md"""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: test-skill
description: "A test skill for unit testing"
version: "1.0.0"
author: "test"
license: "MIT"
tools: ["tool_a", "tool_b"]
triggers:
  - "test"
  - "mock"
examples:
  - input: "test input"
    output: "test output"
---
# Test Skill

## Overview
A test skill for unit testing.
""")
    
    manifest = load_skill(skill_dir)
    
    assert manifest.name == "test-skill"
    assert manifest.description == "A test skill for unit testing"
    assert manifest.version == "1.0.0"
    assert manifest.author == "test"
    assert manifest.license == "MIT"
    assert manifest.tools == ["tool_a", "tool_b"]
    assert manifest.triggers == ["test", "mock"]
    assert len(manifest.examples) == 1
    assert manifest.path == skill_dir


def test_load_skill_discovers_python_implementations(tmp_path):
    """Test that loader discovers .py implementations"""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: test-skill
description: "Test skill"
version: "1.0.0"
tools: ["my_tool"]
---
""")
    
    tool_file = skill_dir / "my_tool.py"
    tool_file.write_text("def my_tool(**kwargs): pass")
    
    manifest = load_skill(skill_dir)
    
    assert "my_tool" in manifest.entry_points
    assert manifest.entry_points["my_tool"] == "my_tool:my_tool"


def test_load_skill_raises_on_missing_skill_md(tmp_path):
    """Test that loader raises ValueError when SKILL.md is missing"""
    skill_dir = tmp_path / "empty-skill"
    skill_dir.mkdir()
    
    with pytest.raises(ValueError, match="No SKILL.md"):
        load_skill(skill_dir)


def test_load_skill_handles_missing_optional_fields(tmp_path):
    """Test that loader handles missing optional frontmatter fields"""
    skill_dir = tmp_path / "minimal-skill"
    skill_dir.mkdir()
    
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: minimal-skill
description: "Minimal skill"
---
""")
    
    manifest = load_skill(skill_dir)
    
    assert manifest.version == "1.0.0"
    assert manifest.author == "unknown"
    assert manifest.license == "MIT"
    assert manifest.tools == []
    assert manifest.triggers == []
    assert manifest.examples == []
