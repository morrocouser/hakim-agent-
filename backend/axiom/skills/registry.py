import json
from pathlib import Path
from typing import Optional
from .loader import load_skill, SkillManifest


class SkillRegistry:
    def __init__(self, skills_root: Path):
        self.skills_root = skills_root
        self.index_path = skills_root / "registry" / "index.json"
        self._skills: dict[str, SkillManifest] = {}
        self._tool_index: dict[str, list[SkillManifest]] = {}
        self._trigger_index: dict[str, list[SkillManifest]] = {}
        self._load_index()

    def _load_index(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        if self.index_path.exists():
            data = json.loads(self.index_path.read_text())
            for item in data.get("skills", []):
                skill_path = self.skills_root / item["path"]
                if skill_path.exists():
                    try:
                        skill = load_skill(skill_path)
                        self._register(skill)
                    except Exception as e:
                        print(f"Failed to load {skill_path}: {e}")
        else:
            self._scan_and_index()

    def _scan_and_index(self):
        if not self.skills_root.exists():
            return

        for skill_dir in self.skills_root.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                try:
                    skill = load_skill(skill_dir)
                    self._register(skill)
                except Exception as e:
                    print(f"Failed to load {skill_dir}: {e}")
        self._save_index()

    def _register(self, skill: SkillManifest):
        self._skills[skill.name] = skill
        for tool in skill.tools:
            self._tool_index.setdefault(tool, []).append(skill)
        for trigger in skill.triggers:
            self._trigger_index.setdefault(trigger, []).append(skill)

    def _save_index(self):
        data = {
            "generated": "2026-08-04",
            "total_skills": len(self._skills),
            "skills": [
                {"name": s.name, "path": str(s.path.relative_to(self.skills_root))}
                for s in self._skills.values()
            ],
        }
        self.index_path.write_text(json.dumps(data, indent=2))

    def refresh(self):
        self._skills.clear()
        self._tool_index.clear()
        self._trigger_index.clear()
        self._scan_and_index()

    def get_skill(self, name: str) -> Optional[SkillManifest]:
        return self._skills.get(name)

    def find_by_tool(self, tool: str) -> list[SkillManifest]:
        return self._tool_index.get(tool, [])

    def find_by_trigger(self, trigger: str) -> list[SkillManifest]:
        return self._trigger_index.get(trigger, [])

    def all_skills(self) -> list[SkillManifest]:
        return list(self._skills.values())
