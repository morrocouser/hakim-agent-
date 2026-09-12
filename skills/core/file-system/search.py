from pathlib import Path


def search(path: str = ".", query: str = "", extension: str = None) -> dict:
    """Search for files containing query"""
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return {"error": f"Directory not found: {path}"}

        results = []
        glob_pattern = f"**/*{extension}" if extension else "**/*"

        for file_path in dir_path.glob(glob_pattern):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if query.lower() in content.lower():
                        lines = content.split("\n")
                        matching_lines = []
                        for i, line in enumerate(lines, 1):
                            if query.lower() in line.lower():
                                matching_lines.append(i)

                        results.append({
                            "path": str(file_path),
                            "matching_lines": matching_lines,
                            "line_count": len(matching_lines),
                        })
                except Exception:
                    pass

        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e)}
