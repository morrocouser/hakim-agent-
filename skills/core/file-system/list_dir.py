from pathlib import Path


def list_dir(path: str = ".", pattern: str = "*") -> dict:
    """List files in directory"""
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return {"error": f"Directory not found: {path}"}

        if not dir_path.is_dir():
            return {"error": f"Not a directory: {path}"}

        files = []
        for item in dir_path.glob(pattern):
            files.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
            })

        return {"files": files, "count": len(files)}
    except Exception as e:
        return {"error": str(e)}
