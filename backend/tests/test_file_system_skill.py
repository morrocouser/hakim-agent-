import pytest
from pathlib import Path
import sys
import tempfile

# Add skills directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "core" / "file-system"))

from read import read
from write import write
from list_dir import list_dir
from search import search


def test_read_file():
    """Test reading file contents"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")

        result = read(str(test_file))

        assert "content" in result
        assert result["content"] == "Hello, World!"


def test_read_not_found():
    """Test reading non-existent file"""
    result = read("/nonexistent/file.txt")
    assert "error" in result


def test_write_file():
    """Test writing file contents"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"

        result = write(str(test_file), "Hello, World!")

        assert result["success"] is True
        assert test_file.read_text() == "Hello, World!"


def test_list_dir():
    """Test listing directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "file1.txt").write_text("a")
        (Path(tmpdir) / "file2.txt").write_text("b")

        result = list_dir(tmpdir)

        assert result["count"] == 2
        assert len(result["files"]) == 2


def test_list_dir_not_found():
    """Test listing non-existent directory"""
    result = list_dir("/nonexistent/dir")
    assert "error" in result


def test_search():
    """Test searching files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "file1.txt").write_text("hello world")
        (Path(tmpdir) / "file2.txt").write_text("foo bar")

        result = search(tmpdir, "hello")

        assert result["count"] == 1
        assert result["results"][0]["path"].endswith("file1.txt")
