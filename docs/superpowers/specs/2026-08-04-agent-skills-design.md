# Agent Skills Architecture Specification

**Date**: 2026-08-04
**Status**: Approved
**Author**: hakimagent team

---

## 1. Overview

### 1.1 Purpose
Build a modular, extensible agent skills framework that enables the hakimagent system to dynamically discover, load, and execute specialized skills for autonomous task execution.

### 1.2 Scope
- **Phase 1**: Implement 10 essential skills with full functionality
- **Runtime**: Python core with FFI/embedding for TypeScript (Deno), Rust (PyO3), Go (CGO)
- **Skill Format**: Standard opencode `SKILL.md` with frontmatter
- **Registry**: Local filesystem-only
- **Execution Model**: In-process plugins

### 1.3 Success Criteria
- All 10 skills load from `SKILL.md` and execute via `ToolRouter`
- Agent completes multi-step tasks: plan → execute → validate
- FFI bridges work for Python + at least one other language (Rust/Go)
- Local registry auto-discovers skills on filesystem changes
- Integration tests pass

---

## 2. Architecture

### 2.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     PilotAgent                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Planner   │  │   Memory    │  │      Router         │  │
│  │   (skill)   │  │  Manager    │  │  (ToolRouter)       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          ▼                                   │
│              ┌─────────────────────┐                         │
│              │    Skill Registry   │                         │
│              │   (local filesystem)│                         │
│              └──────────┬──────────┘                         │
│                         │                                     │
│         ┌───────────────┼───────────────┐                    │
│         ▼               ▼               ▼                    │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │  Python  │    │   Rust   │    │  TypeScript/Go       │
│   │  Skills  │    │  (PyO3)  │    │  (Deno/Node + CGO)   │
│   └──────────┘    └──────────┘    └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Core Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `SkillLoader` | `axiom/skills/loader.py` | Parse SKILL.md, discover implementations |
| `SkillRegistry` | `axiom/skills/registry.py` | Local index, filesystem watching, skill lookup |
| `ToolRouter` | `axiom/skills/router.py` | Intent → skill/tool matching, confidence scoring |
| `SkillExecutor` | `axiom/skills/executor.py` | Load, invoke, validate tool execution |
| `FFI Bridges` | `axiom/skills/ffi/` | PyO3 (Rust), Deno/Node (TS), CGO (Go) |
| `PilotAgent` | `axiom/core/agent.py` | Main loop: plan → execute → validate |

---

## 3. Skill Specification

### 3.1 SKILL.md Format (opencode standard)

```markdown
---
name: planner
description: "Decomposes objectives into executable steps with dependencies"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["task_decompose", "dependency_graph", "schedule"]
triggers:
  - "plan"
  - "decompose"
  - "roadmap"
examples:
  - input: "Build a REST API with authentication"
    output: "tasks: [design_schema, implement_auth, create_endpoints, write_tests]"
---
# Planner Skill

## Overview
Strategic planning and goal decomposition for agent operations.

## Tools

### task_decompose(objective: string) -> Task[]
Breaks down high-level objectives into ordered, dependency-aware tasks.

### dependency_graph(tasks: Task[]) -> Graph
Computes execution order and parallelization opportunities.

### schedule(tasks: Task[], constraints: Constraints) -> Timeline
Generates execution timeline respecting resource constraints.
```

### 3.2 Required Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique skill identifier (kebab-case) |
| `description` | string | Yes | Human-readable purpose |
| `version` | string | Yes | Semantic version |
| `author` | string | No | Author/organization |
| `license` | string | No | SPDX license identifier |
| `tools` | string[] | Yes | List of tool names this skill provides |
| `triggers` | string[] | No | Keywords that activate this skill |
| `examples` | object[] | No | Input/output examples for routing |

### 3.3 Implementation Discovery

Each tool listed in `tools` must have a corresponding implementation file in the skill directory:

```
skill-name/
├── SKILL.md
├── task_decompose.py      # Python implementation (preferred)
├── task_decompose.rs      # Rust implementation (PyO3)
├── task_decompose.ts      # TypeScript (Deno/Node)
├── task_decompose.go      # Go implementation (CGO)
└── lib/                   # Shared utilities
```

Loader priority: `.py` → `.rs` → `.ts` → `.go`

---

## 4. Component Specifications

### 4.1 SkillLoader

```python
# axiom/skills/loader.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml
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
    entry_points: dict[str, str]  # tool_name -> "module:function"
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
        path=skill_dir
    )
```

### 4.2 SkillRegistry

```python
# axiom/skills/registry.py
import json
from pathlib import Path
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .loader import load_skill, SkillManifest

class IndexUpdater(FileSystemEventHandler):
    def __init__(self, registry):
        self.registry = registry
    
    def on_any_event(self, event):
        if event.is_directory:
            return
        if "SKILL.md" in event.src_path:
            self.registry.refresh()

class SkillRegistry:
    def __init__(self, skills_root: Path):
        self.skills_root = skills_root
        self.index_path = skills_root / "registry" / "index.json"
        self._skills: dict[str, SkillManifest] = {}
        self._tool_index: dict[str, list[SkillManifest]] = {}
        self._trigger_index: dict[str, list[SkillManifest]] = {}
        self._load_index()
        self._watch_changes()
    
    def _load_index(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        if self.index_path.exists():
            data = json.loads(self.index_path.read_text())
            for item in data.get("skills", []):
                skill = load_skill(self.skills_root / item["path"])
                self._register(skill)
        else:
            self._scan_and_index()
    
    def _scan_and_index(self):
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
            ]
        }
        self.index_path.write_text(json.dumps(data, indent=2))
    
    def _watch_changes(self):
        observer = Observer()
        observer.schedule(IndexUpdater(self), str(self.skills_root), recursive=True)
        observer.daemon = True
        observer.start()
    
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
```

### 4.3 ToolRouter

```python
# axiom/skills/router.py
from dataclasses import dataclass
from typing import Protocol, Optional
from .registry import SkillRegistry, SkillManifest

class Tool(Protocol):
    async def __call__(self, **kwargs) -> any: ...

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
        self.embedder = embedder  # Optional: for semantic matching
        self._tool_cache: dict[str, Tool] = {}
    
    async def route(self, intent: str, context: dict) -> RouteResult:
        # 1. Exact trigger match
        candidates = self.registry.find_by_trigger(intent.lower())
        if len(candidates) == 1:
            return self._select_tool(candidates[0], intent, context, 0.95)
        
        # 2. Tool name match
        if intent in self.registry._tool_index:
            candidates = self.registry.find_by_tool(intent)
            if len(candidates) == 1:
                return self._select_tool(candidates[0], intent, context, 0.9)
        
        # 3. Keyword overlap on triggers/tools
        candidates = self._keyword_match(intent)
        if candidates:
            return self._score_and_select(candidates, intent, context)
        
        # 4. Semantic matching (if embedder available)
        if self.embedder:
            candidates = await self._semantic_match(intent)
            if candidates:
                return self._score_and_select(candidates, intent, context)
        
        raise ValueError(f"No skill found for intent: {intent}")
    
    def _keyword_match(self, intent: str) -> list[SkillManifest]:
        words = set(intent.lower().split())
        scored = []
        for skill in self.registry.all_skills():
            haystack = " ".join(skill.triggers + skill.tools).lower()
            overlap = len(words & set(haystack.split()))
            if overlap > 0:
                scored.append((overlap, skill))
        scored.sort(reverse=True)
        return [s for _, s in scored[:5]]
    
    async def _semantic_match(self, intent: str) -> list[SkillManifest]:
        if not self.embedder:
            return []
        intent_emb = await self.embedder.embed(intent)
        scored = []
        for skill in self.registry.all_skills():
            text = f"{skill.description} {' '.join(skill.triggers + skill.tools)}"
            skill_emb = await self.embedder.embed(text)
            similarity = cosine_similarity(intent_emb, skill_emb)
            if similarity > 0.7:
                scored.append((similarity, skill))
        scored.sort(reverse=True)
        return [s for _, s in scored[:5]]
    
    def _score_and_select(self, candidates: list[SkillManifest], intent: str, context: dict) -> RouteResult:
        best = candidates[0]
        tool_name = self._select_best_tool(best, intent)
        return self._select_tool(best, intent, context, 0.7)
    
    def _select_best_tool(self, skill: SkillManifest, intent: str) -> str:
        if len(skill.tools) == 1:
            return skill.tools[0]
        # Score tools by keyword overlap
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
            reasoning=f"Matched '{intent}' to {skill.name}.{tool_name} (trigger/tool overlap)"
        )
    
    def _load_tool(self, skill: SkillManifest, tool_name: str) -> Tool:
        cache_key = f"{skill.name}:{tool_name}"
        if cache_key in self._tool_cache:
            return self._tool_cache[cache_key]
        
        entry = skill.entry_points.get(tool_name)
        if not entry:
            raise ValueError(f"No implementation for {tool_name} in {skill.name}")
        
        module_name, func_name = entry.split(":")
        skill_dir = skill.path
        
        # Determine language by file extension
        impl_file = skill_dir / f"{tool_name}.py"
        if impl_file.exists():
            tool = self._load_python_tool(module_name, func_name, skill_dir)
        else:
            impl_file = skill_dir / f"{tool_name}.rs"
            if impl_file.exists():
                tool = self._load_rust_tool(module_name, func_name, skill_dir)
            else:
                impl_file = skill_dir / f"{tool_name}.ts"
                if impl_file.exists():
                    tool = self._load_ts_tool(module_name, func_name, skill_dir)
                else:
                    impl_file = skill_dir / f"{tool_name}.go"
                    if impl_file.exists():
                        tool = self._load_go_tool(module_name, func_name, skill_dir)
                    else:
                        raise ValueError(f"No implementation found for {tool_name}")
        
        self._tool_cache[cache_key] = tool
        return tool
    
    def _load_python_tool(self, module_name: str, func_name: str, skill_dir: Path) -> Tool:
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, skill_dir / f"{module_name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, func_name)
    
    def _load_rust_tool(self, module_name: str, func_name: str, skill_dir: Path) -> Tool:
        import importlib.util
        # Cargo builds to target/release/lib{name}.so
        lib_name = f"lib{skill_dir.name}"
        lib_path = skill_dir / "target" / "release" / f"{lib_name}.so"
        if not lib_path.exists():
            lib_path = skill_dir / "target" / "release" / f"{lib_name}.dylib"
        if not lib_path.exists():
            lib_path = skill_dir / "target" / "release" / f"{lib_name}.dll"
        spec = importlib.util.spec_from_file_location(module_name, lib_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, func_name)
    
    def _load_ts_tool(self, module_name: str, func_name: str, skill_dir: Path) -> Tool:
        import subprocess, json
        class TSTool:
            def __init__(self, skill_dir: Path, tool_name: str):
                self.proc = subprocess.Popen(
                    ["deno", "run", "--allow-all", f"{tool_name}.ts"],
                    cwd=skill_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            
            async def __call__(self, **kwargs) -> any:
                request = {"method": func_name, "params": kwargs}
                self.proc.stdin.write((json.dumps(request) + "\n").encode())
                self.proc.stdin.flush()
                response = json.loads(self.proc.stdout.readline())
                if "error" in response:
                    raise RuntimeError(response["error"])
                return response["result"]
        return TSTool(self, func_name)
    
    def _load_go_tool(self, module_name: str, func_name: str, skill_dir: Path) -> Tool:
        import ctypes, json
        lib_path = skill_dir / f"lib{func_name}.so"
        if not lib_path.exists():
            lib_path = skill_dir / f"{func_name}.dll"
        if not lib_path.exists():
            lib_path = skill_dir / f"{func_name}.dylib"
        lib = ctypes.CDLL(str(lib_path))
        func = getattr(lib, func_name)
        func.argtypes = [ctypes.c_char_p]
        func.restype = ctypes.c_char_p
        return lambda **kwargs: json.loads(func(json.dumps(kwargs).encode()))
```

### 4.4 PilotAgent

```python
# axiom/core/agent.py
from dataclasses import dataclass
from typing import Optional
from axiom.skills.registry import SkillRegistry
from axiom.skills.router import ToolRouter
from axiom.core.memory import MemoryManager

@dataclass
class Task:
    name: str
    intent: str
    params: dict
    dependencies: list[str] = None

@dataclass
class Schedule:
    tasks: list[Task]
    parallel_groups: list[list[str]]

@dataclass
class Result:
    tasks: list[any]
    success: bool
    error: Optional[str] = None

class PilotAgent:
    def __init__(self, skills_root: Path, embedder=None):
        self.registry = SkillRegistry(skills_root)
        self.router = ToolRouter(self.registry, embedder)
        self.memory = MemoryManager()
        self._core_skills = {}
    
    def _load_core_skills(self):
        core_names = ["planner", "memory-manager", "reasoning", "validator"]
        for name in core_names:
            skill = self.registry.get_skill(name)
            if skill:
                self._core_skills[name] = skill
    
    async def execute(self, objective: str, constraints: dict = None) -> Result:
        self._load_core_skills()
        
        # 1. PLAN
        planner_tool = await self._get_tool("planner", "task_decompose")
        tasks_data = await planner_tool(objective=objective)
        tasks = [Task(**t) for t in tasks_data]
        
        schedule_tool = await self._get_tool("planner", "schedule")
        schedule_data = await schedule_tool(tasks=tasks, constraints=constraints or {})
        schedule = Schedule(**schedule_data)
        
        # 2. EXECUTE
        results = []
        executed = set()
        
        for group in schedule.parallel_groups:
            group_tasks = [t for t in schedule.tasks if t.name in group]
            if len(group_tasks) == 1:
                result = await self._execute_task(group_tasks[0], results)
                results.append(result)
                executed.add(group_tasks[0].name)
            else:
                # Parallel execution
                import asyncio
                group_results = await asyncio.gather(*[
                    self._execute_task(t, results) for t in group_tasks
                ])
                results.extend(group_results)
                executed.update(t.name for t in group_tasks)
        
        # 3. VALIDATE
        validator = await self._get_tool("validator", "validate")
        all_valid = True
        for result in results:
            if hasattr(result, 'ok') and not result.ok:
                all_valid = False
                break
            elif isinstance(result, dict) and not result.get("ok", True):
                all_valid = False
                break
        
        if not all_valid:
            fix_tool = await self._get_tool("reasoning", "recover")
            results = await fix_tool(failed_results=results, objective=objective)
        
        return Result(tasks=results, success=all_valid)
    
    async def _execute_task(self, task: Task, history: list) -> any:
        tool = await self.router.route(task.intent, {
            "task": task.__dict__,
            "history": history,
            "memory": self.memory.get_context()
        })
        return await tool.tool(**task.params)
    
    async def _get_tool(self, skill_name: str, tool_name: str):
        skill = self.registry.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Core skill not found: {skill_name}")
        return self.router._load_tool(skill, tool_name)
```

---

## 5. FFI Bridge Specifications

### 5.1 Rust (PyO3)
```rust
// skill-name/src/lib.rs
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

#[pyfunction]
fn task_decompose(objective: String) -> PyResult<String> {
    let tasks = vec![
        Task { name: "design".to_string(), description: "Design schema".to_string() },
        Task { name: "implement".to_string(), description: "Implement logic".to_string() },
    ];
    Ok(serde_json::to_string(&tasks).unwrap())
}

#[pymodule]
fn planner(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(task_decompose, m)?)?;
    Ok(())
}

#[derive(Serialize, Deserialize)]
struct Task {
    name: String,
    description: String,
}
```

```toml
# Cargo.toml
[package]
name = "planner"
version = "0.1.0"
edition = "2021"

[lib]
name = "planner"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.22", features = ["extension-module"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
```

### 5.2 TypeScript (Deno)
```typescript
// planner.ts
interface Task {
  name: string;
  description: string;
}

async function task_decompose(params: { objective: string }): Promise<Task[]> {
  const objective = params.objective;
  return [
    { name: "design", description: `Design schema for: ${objective}` },
    { name: "implement", description: `Implement logic for: ${objective}` },
    { name: "test", description: `Write tests for: ${objective}` },
  ];
}

if (import.meta.main) {
  for await (const line of Deno.stdin.readable) {
    const request = JSON.parse(line);
    const result = await task_decompose(request.params);
    console.log(JSON.stringify({ result }));
  }
}
```

### 5.3 Go (CGO)
```go
// planner.go
package main

import (
	"encoding/json"
	"C"
)

type Task struct {
	Name        string `json:"name"`
	Description string `json:"description"`
}

type Params struct {
	Objective string `json:"objective"`
}

type Result struct {
	Tasks []Task `json:"tasks"`
}

//export task_decompose
func task_decompose(input *C.char) *C.char {
	var params Params
	json.Unmarshal([]byte(C.GoString(input)), &params)
	
	result := Result{
		Tasks: []Task{
			{Name: "design", Description: "Design schema for: " + params.Objective},
			{Name: "implement", Description: "Implement logic for: " + params.Objective},
		},
	}
	
	output, _ := json.Marshal(result)
	return C.CString(string(output))
}

func main() {}
```

---

## 6. Directory Structure

```
hakimagent/
├── skills/
│   ├── core/
│   │   ├── planner/
│   │   │   ├── SKILL.md
│   │   │   ├── task_decompose.py
│   │   │   ├── dependency_graph.py
│   │   │   └── schedule.py
│   │   ├── memory-manager/
│   │   ├── reasoning/
│   │   ├── tool-router/
│   │   ├── web-research/
│   │   ├── code-expert/
│   │   ├── terminal/
│   │   ├── file-system/
│   │   ├── github-manager/
│   │   └── validator/
│   ├── registry/
│   │   ├── index.json
│   │   └── cache/
│   └── community/
│
├── backend/
│   ├── axiom/
│   │   ├── skills/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py
│   │   │   ├── registry.py
│   │   │   ├── router.py
│   │   │   ├── executor.py
│   │   │   └── ffi/
│   │   │       ├── __init__.py
│   │   │       ├── rust_bridge.py
│   │   │       ├── ts_bridge.py
│   │   │       └── go_bridge.py
│   │   ├── core/
│   │   │   ├── agent.py
│   │   │   └── __init__.py
│   │   ├── api/
│   │   │   └── routes_skills.py
│   │   └── tests/
│   │       ├── test_skill_loader.py
│   │       ├── test_skill_registry.py
│   │       ├── test_tool_router.py
│   │       └── test_pilot_agent.py
│   └── pyproject.toml
│
└── docs/superpowers/specs/2026-08-04-agent-skills-design.md
```

---

## 7. Integration with Existing hakimagent

### 7.1 Reused Components
- `MemoryManager` → Extended for skill context
- `ReActLoop` → Enhanced with `ToolRouter`
- `WebSearchTool` → Available as skill tool
- `CodeExecutor` → Available as skill tool
- `FileManager` → Available as skill tool
- `ErrorLog` → Available as skill tool

### 7.2 New API Endpoints
```python
# axiom/api/routes_skills.py
from fastapi import APIRouter, HTTPException
from axiom.skills.registry import SkillRegistry
from axiom.skills.router import ToolRouter

router = APIRouter(prefix="/api/v1/skills")
registry = SkillRegistry(Path("skills"))
tool_router = ToolRouter(registry)

@router.get("/")
async def list_skills():
    return {"skills": [s.name for s in registry.all_skills()]}

@router.get("/{name}")
async def get_skill(name: str):
    skill = registry.get_skill(name)
    if not skill:
        raise HTTPException(404, "Skill not found")
    return skill.__dict__

@router.post("/{name}/{tool}/invoke")
async def invoke_tool(name: str, tool: str, params: dict):
    skill = registry.get_skill(name)
    if not skill:
        raise HTTPException(404, "Skill not found")
    if tool not in skill.tools:
        raise HTTPException(404, "Tool not found in skill")
    router_tool = tool_router._load_tool(skill, tool)
    result = await router_tool(**params)
    return {"result": result}
```

### 7.3 Configuration
```python
# axiom/config.py (extend)
SKILLS_ROOT = Path(os.getenv("SKILLS_ROOT", "skills")).resolve()
SKILLS_ENABLED = os.getenv("SKILLS_ENABLED", "true").lower() == "true"
```

---

## 8. Testing Strategy

### 8.1 Unit Tests
- `test_skill_loader.py` - SKILL.md parsing, entry point discovery
- `test_skill_registry.py` - Indexing, lookup, filesystem watching
- `test_tool_router.py` - Trigger matching, tool selection, confidence scoring
- `test_pilot_agent.py` - Plan → execute → validate flow

### 8.2 Integration Tests
```python
# test_skills_integration.py
async def test_full_agent_flow():
    agent = PilotAgent(Path("skills"))
    result = await agent.execute(
        "Create a Python function that calculates fibonacci numbers with tests"
    )
    assert result.success
    assert len(result.tasks) >= 3  # design, implement, test
```

### 8.3 FFI Tests
- `test_rust_bridge.py` - PyO3 loading and function calls
- `test_ts_bridge.py` - Deno subprocess communication
- `test_go_bridge.py` - CGO shared library calls

---

## 9. Phase 1 Implementation Plan

| Week | Task | Deliverable |
|------|------|-------------|
| 1 | SkillLoader + SkillRegistry + ToolRouter (Python) | Skills auto-discover, route by trigger/tool |
| 2 | Planner + Memory Manager (Python + Rust) | Task decomposition, context persistence |
| 3 | Reasoning + Validator (Python) | Strategy selection, output verification |
| 4 | File System + Terminal (Go) | Project ops, command execution |
| 5 | Code Expert + Web Research (TypeScript) | Code gen/review, web search |
| 6 | GitHub Manager + Integration Tests | Repo management, E2E validation |

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PyO3 version conflicts | Medium | High | Pin pyo3 version; test in CI |
| Deno subprocess overhead | Low | Medium | Pool connections; reuse processes |
| CGO cross-compilation | Medium | High | Use Docker for builds; test on Linux/macOS/Windows |
| Skill version conflicts | Low | Medium | Semantic versioning; registry validates compatibility |
| Filesystem watch failures | Low | Medium | Fallback to manual refresh; polling option |

---

## 11. Appendix: Example SKILL.md Files

### 10.1 Planner
```markdown
---
name: planner
description: "Decomposes objectives into executable steps with dependencies"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["task_decompose", "dependency_graph", "schedule"]
triggers:
  - "plan"
  - "decompose"
  - "roadmap"
  - "break down"
examples:
  - input: "Build a REST API with authentication"
    output: "tasks: [design_schema, implement_auth, create_endpoints, write_tests]"
---
# Planner Skill

## Overview
Strategic planning and goal decomposition for agent operations.

## Tools

### task_decompose(objective: string) -> Task[]
Breaks down high-level objectives into ordered, dependency-aware tasks.

### dependency_graph(tasks: Task[]) -> Graph
Computes execution order and parallelization opportunities.

### schedule(tasks: Task[], constraints: Constraints) -> Timeline
Generates execution timeline respecting resource constraints.
```

### 10.2 Memory Manager
```markdown
---
name: memory-manager
description: "Manages agent context, conversation history, and knowledge persistence"
version: "1.0.0"
tools: ["store", "retrieve", "search", "summarize", "clear"]
triggers:
  - "remember"
  - "recall"
  - "context"
  - "history"
---
```

### 10.3 Tool Router
```markdown
---
name: tool-router
description: "Routes user intent to the appropriate skill and tool"
version: "1.0.0"
tools: ["route", "list_tools", "describe_tool"]
triggers:
  - "route"
  - "which tool"
  - "what skill"
---
```

### 10.4 Validator
```markdown
---
name: validator
description: "Verifies task results meet quality criteria before returning to user"
version: "1.0.0"
tools: ["validate", "check_syntax", "run_tests", "check_security"]
triggers:
  - "validate"
  - "verify"
  - "check"
---
```

---

*End of Specification*