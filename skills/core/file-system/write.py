from pathlib import Path


def write(path: str, content: str, encoding: str = "utf-8") -> dict:
    """Write content to file"""
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding=encoding)
        return {"success": True, "size": len(content)}
    except Exception as e:
        return {"error": str(e)}
