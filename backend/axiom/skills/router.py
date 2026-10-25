import re
from dataclasses import dataclass
from typing import Protocol, Optional, Any
from pathlib import Path
from .registry import SkillRegistry, SkillManifest
from axiom.logging_setup import log


class Tool(Protocol):
    async def __call__(self, **kwargs) -> Any: ...


@dataclass
class RouteResult:
    tool: Tool
    skill_name: str
    tool_name: str
    confidence: float
    reasoning: str


class ToolRouter:
    def __init__(self, registry: SkillRegistry, embedder=None):
        self.registry = registry
        self.embedder = embedder
        self._tool_cache: dict[str, Tool] = {}

    async def route(self, intent: str, context: dict) -> RouteResult:
        log.info("   🔀 Skill Router — intent: %s", intent[:60])
        # 1. Exact trigger match
        candidates = self.registry.find_by_trigger(intent.lower())
        if len(candidates) == 1:
            log.info("   🔀 Match exact par trigger → %s", candidates[0].name)
            return self._select_tool(candidates[0], intent, context, 0.95)
        elif len(candidates) > 1:
            log.info("   🔀 %s triggers correspondants → scoring", len(candidates))
            return self._score_and_select(candidates, intent, context)

        # 2. Tool name match
        if intent in self.registry._tool_index:
            candidates = self.registry.find_by_tool(intent)
            if len(candidates) == 1:
                log.info("   🔀 Match par nom d'outil → %s", candidates[0].name)
                return self._select_tool(candidates[0], intent, context, 0.9)
            elif len(candidates) > 1:
                log.info("   🔀 %s outils correspondants → scoring", len(candidates))
                return self._score_and_select(candidates, intent, context)

        # 3. Keyword overlap on triggers/tools
        candidates = self._keyword_match(intent)
        if candidates:
            log.info("   🔀 %s matches par mots-clés → scoring", len(candidates))
            return self._score_and_select(candidates, intent, context)

        # 4. Semantic matching (if embedder available)
        if self.embedder:
            candidates = await self._semantic_match(intent)
            if candidates:
                log.info("   🔀 %s matches sémantiques → scoring", len(candidates))
                return self._score_and_select(candidates, intent, context)

        log.warning("   🔀 Aucun skill trouvé pour: %s", intent[:60])
        raise ValueError(f"No skill found for intent: {intent}")

    def _score_skill(self, skill: SkillManifest, intent: str) -> int:
        """Score how well an intent matches a skill's triggers and tool names.

        Multi-word triggers ("read file", "pull request") count when the whole
        phrase appears in the intent, and weigh more than single words. Tool
        names are split on "_" so "decompose" matches "task_decompose".
        """
        intent_lower = intent.lower()
        words = set(re.findall(r"\w+", intent_lower))
        score = 0
        for trigger in skill.triggers:
            trigger = trigger.lower().strip()
            if " " in trigger:
                if re.search(rf"\b{re.escape(trigger)}\b", intent_lower):
                    score += 2 * len(trigger.split())
            elif trigger in words:
                score += 2
        for tool in skill.tools:
            score += len(words & set(tool.lower().split("_")))
        return score

    def _keyword_match(self, intent: str) -> list[SkillManifest]:
        scored = []
        for skill in self.registry.all_skills():
            score = self._score_skill(skill, intent)
            if score > 0:
                scored.append((score, skill))
        # sort() is stable, so equal scores keep registry order.
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:5]]

    async def _semantic_match(self, intent: str) -> list[SkillManifest]:
        if not self.embedder:
            return []
        intent_emb = await self.embedder.embed(intent)
        scored = []
        for skill in self.registry.all_skills():
            text = f"{skill.description} {' '.join(skill.triggers + skill.tools)}"
            skill_emb = await self.embedder.embed(text)
            similarity = self._cosine_similarity(intent_emb, skill_emb)
            if similarity > 0.7:
                scored.append((similarity, skill))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:5]]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        return dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0

    def _score_and_select(self, candidates: list[SkillManifest], intent: str, context: dict) -> RouteResult:
        scores = [self._score_skill(c, intent) for c in candidates]
        best_index = max(range(len(candidates)), key=lambda i: scores[i])
        best_score = scores[best_index]
        # More evidence → more confidence, capped below the exact-match levels.
        confidence = min(0.85, 0.5 + 0.1 * best_score)
        if scores.count(best_score) > 1:
            # Several skills are equally plausible: the pick is a coin flip.
            confidence = min(confidence, 0.6)
        return self._select_tool(candidates[best_index], intent, context, confidence)

    def _select_best_tool(self, skill: SkillManifest, intent: str) -> str:
        if len(skill.tools) == 1:
            return skill.tools[0]
        words = set(intent.lower().split())
        best_tool = max(skill.tools, key=lambda t: len(words & set(t.split("_"))))
        return best_tool

    def _select_tool(self, skill: SkillManifest, intent: str, context: dict, confidence: float) -> RouteResult:
        tool_name = self._select_best_tool(skill, intent)
        tool = self._load_tool(skill, tool_name)
        return RouteResult(
            tool=tool,
            skill_name=skill.name,
            tool_name=tool_name,
            confidence=confidence,
            reasoning=f"Matched '{intent}' to {skill.name}.{tool_name} (trigger/tool overlap, confidence {confidence:.2f})",
        )

    def _load_tool(self, skill: SkillManifest, tool_name: str) -> Tool:
        cache_key = f"{skill.name}:{tool_name}"
        if cache_key in self._tool_cache:
            return self._tool_cache[cache_key]

        entry = skill.entry_points.get(tool_name)
        if not entry:
            # Return a placeholder tool if no implementation exists
            async def placeholder_tool(**kwargs):
                return {"error": f"No implementation for {tool_name} in {skill.name}"}
            return placeholder_tool

        module_name, func_name = entry.split(":")
        skill_dir = skill.path

        # Load Python implementation
        impl_file = skill_dir / f"{tool_name}.py"
        if impl_file.exists():
            tool = self._load_python_tool(module_name, func_name, skill_dir)
            self._tool_cache[cache_key] = tool
            return tool

        # Return placeholder for other languages
        async def placeholder_tool(**kwargs):
            return {"error": f"Implementation for {tool_name} not available yet"}
        return placeholder_tool

    def _load_python_tool(self, module_name: str, func_name: str, skill_dir: Path) -> Tool:
        import importlib.util
        import asyncio
        import inspect
        spec = importlib.util.spec_from_file_location(module_name, skill_dir / f"{module_name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        func = getattr(module, func_name)

        if inspect.iscoroutinefunction(func):
            return func

        async def _async_wrapper(**kwargs):
            return func(**kwargs)
        return _async_wrapper
