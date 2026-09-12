import os
import tempfile
import pytest
from pathlib import Path

from axiom.cli_engine import SnapshotManager, ContextManager, AxiomCLIEngine


def test_snapshot_and_rollback():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mgr = SnapshotManager(tmpdir)

        # 1. Test avec fichier existant
        sample_file = tmp_path / "test.py"
        sample_file.write_text("print('version 1')", encoding="utf-8")

        # Capture snapshot
        bak = mgr.capture(str(sample_file))
        assert bak is not None
        assert Path(bak).exists()

        # Modifier le fichier
        sample_file.write_text("print('version 2')", encoding="utf-8")
        assert sample_file.read_text(encoding="utf-8") == "print('version 2')"

        # Rollback
        ok, msg = mgr.rollback()
        assert ok is True
        assert sample_file.read_text(encoding="utf-8") == "print('version 1')"


def test_snapshot_new_file_rollback():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mgr = SnapshotManager(tmpdir)

        new_file = tmp_path / "new_created.py"

        # Capture pour nouveau fichier
        bak = mgr.capture(str(new_file))
        assert bak is None  # Fichier n'existait pas encore

        # Écrire nouveau fichier
        new_file.write_text("x = 42", encoding="utf-8")
        assert new_file.exists()

        # Rollback doit le supprimer
        ok, msg = mgr.rollback()
        assert ok is True
        assert not new_file.exists()


def test_claude_md_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Regle: Toujours utiliser des types stricts.", encoding="utf-8")

        ctx_mgr = ContextManager(tmpdir)
        prompt = ctx_mgr.load_system_prompt()

        assert "CLAUDE.md" in prompt
        assert "Regle: Toujours utiliser des types stricts." in prompt


def test_history_compaction():
    with tempfile.TemporaryDirectory() as tmpdir:
        ctx_mgr = ContextManager(tmpdir)
        history = [
            {"role": "user", "content": "Initial prompt"},
            {"role": "assistant", "content": "Step 1"},
            {"role": "tool", "content": "Long tool output 1"},
            {"role": "assistant", "content": "Step 2"},
            {"role": "tool", "content": "Long tool output 2"},
            {"role": "assistant", "content": "Step 3"},
        ]

        compacted = ctx_mgr.compact_history(history)
        assert len(compacted) < len(history)
        assert compacted[0]["content"] == "Initial prompt"
        assert compacted[1]["role"] == "system"
        assert "Historique compacté" in compacted[1]["content"]


@pytest.mark.asyncio
async def test_engine_tool_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = AxiomCLIEngine(tmpdir)
        engine.auto_approve = True

        # Write file tool
        ok, msg = await engine.execute_tool_call("write_file", {"path": "hello.py", "content": "def hello(): pass"})
        assert ok is True
        assert (Path(tmpdir) / "hello.py").exists()

        # Read file tool
        ok, content = await engine.execute_tool_call("read_file", {"path": "hello.py"})
        assert ok is True
        assert "def hello(): pass" in content

        # Edit file tool
        ok, msg = await engine.execute_tool_call("edit_file", {
            "path": "hello.py",
            "old_text": "def hello(): pass",
            "new_text": "def hello(): return 'world'",
        })
        assert ok is True

        # Verify content
        ok, content = await engine.execute_tool_call("read_file", {"path": "hello.py"})
        assert "return 'world'" in content

        # Test Rollback
        ok_rb, msg_rb = engine.rollback()
        assert ok_rb is True
        ok, content = await engine.execute_tool_call("read_file", {"path": "hello.py"})
        assert "def hello(): pass" in content
