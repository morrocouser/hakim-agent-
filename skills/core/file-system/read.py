from pathlib import Path


def read(path: str, encoding: str = "utf-8") -> dict:
    """Read file contents"""
    try:
        file_path = Path(path)
        if not file_path.exists():
            return {"error": f"File not found: {path}"}

        if not file_path.is_file():
            return {"error": f"Not a file: {path}"}

        content = file_path.read_text(encoding=encoding)
        return {"content": content, "size": len(content)}
    except Exception as e:
        return {"error": str(e)}
