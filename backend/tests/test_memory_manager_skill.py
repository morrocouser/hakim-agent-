import pytest
from pathlib import Path
import sys
import tempfile
import importlib.util

# Import each module directly to avoid name collisions
def _import_from(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

_base = Path(__file__).parent.parent.parent / "skills" / "core" / "memory-manager"
_store_mod = _import_from("mm_store", _base / "store.py")
_retrieve_mod = _import_from("mm_retrieve", _base / "retrieve.py")
_search_mod = _import_from("mm_search", _base / "search.py")
_summarize_mod = _import_from("mm_summarize", _base / "summarize.py")
_clear_mod = _import_from("mm_clear", _base / "clear.py")

MemoryStore = _store_mod.MemoryStore
MemoryRetriever = _retrieve_mod.MemoryRetriever
MemorySearcher = _search_mod.MemorySearcher
summarize = _summarize_mod.summarize
MemoryClearer = _clear_mod.MemoryClearer


def test_store_and_retrieve():
    """Test storing and retrieving values"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_memory.json"

        store = MemoryStore(storage_path)
        store.store("test_key", "test_value", {"category": "test"})

        retriever = MemoryRetriever(storage_path)
        result = retriever.retrieve("test_key")

        assert result == "test_value"


def test_store_returns_true():
    """Test that store returns True on success"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_memory.json"

        store = MemoryStore(storage_path)
        result = store.store("key", "value")

        assert result is True


def test_retrieve_missing_key():
    """Test retrieving a key that doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_memory.json"

        store = MemoryStore(storage_path)
        retriever = MemoryRetriever(storage_path)
        result = retriever.retrieve("nonexistent")

        assert result is None


def test_search():
    """Test searching memory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_memory.json"

        store = MemoryStore(storage_path)
        store.store("language", "python", {"type": "preference"})
        store.store("framework", "fastapi", {"type": "preference"})

        searcher = MemorySearcher(storage_path)
        results = searcher.search("python")

        assert len(results) == 1
        assert results[0]["key"] == "language"


def test_search_no_results():
    """Test searching with no matches"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_memory.json"

        store = MemoryStore(storage_path)
        store.store("language", "python")

        searcher = MemorySearcher(storage_path)
        results = searcher.search("rust")

        assert len(results) == 0


def test_summarize():
    """Test context summarization"""
    context = {
        "conversation": [{"role": "user", "content": "hello"}],
        "tasks": ["task1", "task2"],
        "current_task": "testing",
    }

    summary = summarize(context)

    assert "1 messages" in summary
    assert "2 tasks" in summary
    assert "testing" in summary


def test_summarize_empty():
    """Test summarizing empty context"""
    result = summarize({})
    assert result == "No context available"


def test_clear():
    """Test clearing memory entries"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_memory.json"

        store = MemoryStore(storage_path)
        store.store("test1", "value1")
        store.store("test2", "value2")
        store.store("other", "value3")

        clearer = MemoryClearer(storage_path)
        cleared = clearer.clear("test*")

        assert cleared is True

        retriever = MemoryRetriever(storage_path)
        assert retriever.retrieve("test1") is None
        assert retriever.retrieve("test2") is None
        assert retriever.retrieve("other") == "value3"


def test_clear_no_match():
    """Test clearing with pattern that matches nothing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_memory.json"

        store = MemoryStore(storage_path)
        store.store("key", "value")

        clearer = MemoryClearer(storage_path)
        cleared = clearer.clear("nonexistent*")

        assert cleared is False
