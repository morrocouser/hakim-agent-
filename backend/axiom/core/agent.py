from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path
from axiom.logging_setup import log
from axiom.skills.registry import SkillRegistry
from axiom.skills.router import ToolRouter


@dataclass
class Task:
    name: str
    intent: str
    params: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class Result:
    tasks: list[Any] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


class PilotAgent:
    def __init__(self, skills_root: Path, embedder=None):
        self.registry = SkillRegistry(skills_root)
        self.router = ToolRouter(self.registry, embedder)
        self._memory = {}
        self._core_skills = {}

    def _load_core_skills(self):
        core_names = ["planner", "memory-manager", "reasoning", "validator"]
        for name in core_names:
            skill = self.registry.get_skill(name)
            if skill:
                self._core_skills[name] = skill

    def _get_tool(self, skill_name: str, tool_name: str):
        skill = self.registry.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Core skill not found: {skill_name}")
        return self.router._load_tool(skill, tool_name)

    async def execute(self, objective: str, constraints: dict = None) -> Result:
        log.info("🤖 PILOT AGENT démarré — objectif: %s", objective[:80])
        self._load_core_skills()
        log.info("   Compétences chargées: %s", list(self._core_skills.keys()))

        try:
            # 1. PLAN
            log.info("   📋 ÉTAPE 1/3 : PLANIFICATION...")
            tasks = [Task(name="execute", intent=objective, params={})]

            planner_skill = self.registry.get_skill("planner")
            if planner_skill:
                try:
                    tool = self.router._load_tool(planner_skill, "task_decompose")
                    tasks_data = await tool(objective=objective)
                    if isinstance(tasks_data, list):
                        tasks = [Task(**t) if isinstance(t, dict) else t for t in tasks_data]
                except Exception as e:
                    log.warning("Erreur lors de la planification: %s", str(e))
            log.info("   📋 %s tâche(s) planifiée(s)", len(tasks))

            # 2. EXECUTE
            log.info("   ⚙️  ÉTAPE 2/3 : EXÉCUTION...")
            results = []
            executed = set()

            for task in tasks:
                task_name = task.name if hasattr(task, "name") else str(task)
                if task_name not in executed:
                    log.info("   ⚙️  Tâche: %s", task_name)
                    result = await self._execute_task(task, results)
                    results.append(result)
                    executed.add(task_name)
            log.info("   ⚙️  %s résultat(s) obtenu(s)", len(results))

            # 3. VALIDATE
            log.info("   ✅ ÉTAPE 3/3 : VALIDATION...")
            all_valid = True
            validator_skill = self.registry.get_skill("validator")
            if validator_skill:
                try:
                    validate_tool = self.router._load_tool(validator_skill, "validate")
                    for result in results:
                        validation = await validate_tool(result=result, criteria={})
                        if not validation.get("valid", True):
                            all_valid = False
                            break
                except Exception as e:
                    log.warning("Erreur lors de la validation: %s", str(e))
            log.info("   ✅ Validation: %s", "✅ OK" if all_valid else "❌ ÉCHEC")
            return Result(tasks=results, success=all_valid)
        except Exception as e:
            return Result(tasks=[], success=False, error=str(e))

    async def _execute_task(self, task: Task, history: list) -> Any:
        try:
            route_result = await self.router.route(task.intent, {
                "task": task.__dict__ if hasattr(task, "__dict__") else {"name": str(task)},
                "history": history,
                "memory": self._memory,
            })
            params = task.params if hasattr(task, "params") else {}
            return await route_result.tool(**params)
        except Exception as e:
            return {"error": str(e), "task": str(task)}
