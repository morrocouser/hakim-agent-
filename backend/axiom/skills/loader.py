from dataclasses import dataclass
from pathlib import Path
import frontmatter


@dataclass
class SkillManifest:
    name: str
    description: str
    version: str
    author: str
    license: str
    tools: list[str]
    triggers: list[str]
    examples: list[dict]
    entry_points: dict[str, str]
    path: Path


def load_skill(skill_dir: Path) -> SkillManifest:
    """Load skill from directory containing SKILL.md"""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValueError(f"No SKILL.md in {skill_dir}")

    post = frontmatter.load(skill_md)
    fm = post.metadata

    entry_points = {}
    for tool in fm.get("tools", []):
        for ext in [".py", ".rs", ".ts", ".go"]:
            impl = skill_dir / f"{tool}{ext}"
            if impl.exists():
                entry_points[tool] = f"{impl.stem}:{tool}"
                break

    return SkillManifest(
        name=fm["name"],
        description=fm["description"],
        version=fm.get("version", "1.0.0"),
        author=fm.get("author", "unknown"),
        license=fm.get("license", "MIT"),
        tools=fm.get("tools", []),
        triggers=fm.get("triggers", []),
        examples=fm.get("examples", []),
        entry_points=entry_points,
        path=skill_dir,
    )
