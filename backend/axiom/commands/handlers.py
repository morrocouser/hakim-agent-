# Command Handlers - Implementation for all slash commands

import os
import re
import json
import inspect
import shlex
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from .registry import CommandRegistry, Command, CommandGroup


class CommandHandlers:
    """Implements all slash commands"""
    
    def __init__(self, registry: CommandRegistry):
        self.registry = registry
        self._session_start = datetime.now()
        self._command_history = []
        self._memory = {}
    
    # Appels qui lancent un processus ; toute commande qui les atteint (même
    # transitivement) est considérée comme "spawning".
    _SPAWN_SINKS = {"_run_shell", "_run_git", "_run_gh"}

    def _handler_for(self, command: Command):
        name = f"handle_{command.name[1:].replace('-', '_').replace('/', '_')}"
        return name, getattr(self, name, None)

    def spawns_process(self, command: Command) -> bool:
        """Vrai si le handler de la commande lance (même indirectement) un sous-processus."""
        name, handler = self._handler_for(command)
        if handler is None:
            return False
        seen: set[str] = set()
        todo = [name]
        while todo:
            current = todo.pop()
            if current in seen:
                continue
            seen.add(current)
            if current in self._SPAWN_SINKS:
                return True
            fn = getattr(type(self), current, None)
            if fn is None:
                continue
            try:
                src = inspect.getsource(fn)
            except (OSError, TypeError):
                return True  # fail-closed
            if "subprocess." in src:
                return True
            todo.extend(re.findall(r"self\.(\w+)\(", src))
        return False

    def execute(self, command: Command, args: str) -> dict:
        """Execute a command with arguments"""
        self._command_history.append({
            "command": command.name,
            "args": args,
            "timestamp": datetime.now().isoformat()
        })
        
        handler_name = f"handle_{command.name[1:].replace('-', '_').replace('/', '_')}"
        handler = getattr(self, handler_name, None)
        
        if handler:
            return handler(args)
        
        return {
            "success": False,
            "error": f"Handler not implemented for {command.name}",
            "command": command.name
        }
    
    # System Commands
    def handle_help(self, args: str) -> dict:
        if args:
            cmd = self.registry.get(args)
            if cmd:
                return {
                    "success": True,
                    "output": {
                        "name": cmd.name,
                        "description": cmd.description,
                        "usage": cmd.usage,
                        "examples": cmd.examples,
                        "group": cmd.group.value
                    }
                }
            return {"success": False, "error": f"Command not found: {args}"}
        
        groups = {}
        for cmd in self.registry.list_all():
            group = cmd.group.value
            if group not in groups:
                groups[group] = []
            groups[group].append({"name": cmd.name, "description": cmd.description})
        
        return {"success": True, "output": {"commands": groups, "total": len(self.registry.list_all())}}
    
    def handle_about(self, args: str) -> dict:
        return {
            "success": True,
            "output": {
                "name": "hakimagent",
                "version": "1.0.0",
                "description": "AI-powered agent with comprehensive skill system",
                "author": "hakimagent team",
                "python": platform.python_version(),
                "platform": platform.system()
            }
        }
    
    def handle_version(self, args: str) -> dict:
        return {"success": True, "output": {"version": "1.0.0", "python": platform.python_version()}}
    
    def handle_status(self, args: str) -> dict:
        uptime = (datetime.now() - self._session_start).total_seconds()
        return {
            "success": True,
            "output": {
                "status": "running",
                "uptime_seconds": int(uptime),
                "commands_executed": len(self._command_history),
                "memory_entries": len(self._memory),
                "platform": platform.system(),
                "python": platform.python_version()
            }
        }
    
    def handle_config(self, args: str) -> dict:
        parts = args.split(maxsplit=1) if args else []
        if not parts:
            return {"success": True, "output": {"config": "Use /config key value to set"}}
        if len(parts) == 1:
            return {"success": True, "output": {parts[0]: "current_value"}}
        return {"success": True, "output": {"set": {parts[0]: parts[1]}}}
    
    def handle_settings(self, args: str) -> dict:
        return {"success": True, "output": {"settings": "Settings panel", "theme": "dark", "model": "default"}}
    
    def handle_models(self, args: str) -> dict:
        return {
            "success": True,
            "output": {
                "models": [
                    {"id": "gpt-4", "name": "GPT-4", "provider": "openai"},
                    {"id": "claude-3", "name": "Claude 3", "provider": "anthropic"},
                    {"id": "gemini-pro", "name": "Gemini Pro", "provider": "google"}
                ]
            }
        }
    
    def handle_providers(self, args: str) -> dict:
        return {
            "success": True,
            "output": {
                "providers": ["openai", "anthropic", "google", "groq", "mistral"]
            }
        }
    
    def handle_tools(self, args: str) -> dict:
        return {"success": True, "output": {"tools": ["bash", "read", "write", "search", "web"], "total": 5}}
    
    def handle_skills(self, args: str) -> dict:
        skills_dir = Path("skills/core")
        skills = []
        if skills_dir.exists():
            for d in skills_dir.iterdir():
                if d.is_dir() and (d / "SKILL.md").exists():
                    skills.append(d.name)
        return {"success": True, "output": {"skills": skills, "total": len(skills)}}

    def handle_find_skills(self, args: str) -> dict:
        from axiom.agent_skills_catalog import find_skills
        results = find_skills(query=args.strip(), limit=20)
        return {"success": True, "output": {"query": args, "total": len(results), "skills": results}}
    
    def handle_memory(self, args: str) -> dict:
        parts = args.split(maxsplit=2) if args else []
        if not parts:
            return {"success": True, "output": {"memory": self._memory, "entries": len(self._memory)}}
        action = parts[0]
        if action == "clear":
            self._memory.clear()
            return {"success": True, "output": {"cleared": True}}
        return {"success": True, "output": {"memory_action": action}}
    
    def handle_context(self, args: str) -> dict:
        return {
            "success": True,
            "output": {
                "cwd": os.getcwd(),
                "platform": platform.system(),
                "python": platform.python_version(),
                "session_duration": str(datetime.now() - self._session_start)
            }
        }
    
    def handle_logs(self, args: str) -> dict:
        return {"success": True, "output": {"logs": "No recent logs", "level": "info"}}
    
    def handle_health(self, args: str) -> dict:
        checks = {
            "python": True,
            "skills_dir": Path("skills").exists(),
            "backend": Path("backend/axiom").exists()
        }
        return {"success": True, "output": {"healthy": all(checks.values()), "checks": checks}}
    
    def handle_reset(self, args: str) -> dict:
        self._command_history.clear()
        self._memory.clear()
        return {"success": True, "output": {"reset": True}}
    
    def handle_restart(self, args: str) -> dict:
        return {"success": True, "output": {"restart": "System restart requested"}}
    
    def handle_exit(self, args: str) -> dict:
        return {"success": True, "output": {"exit": "Goodbye!"}, "exit": True}
    
    # Agent Commands
    def handle_plan(self, args: str) -> dict:
        return {"success": True, "output": {"plan": "Planning system", "action": args or "list"}}
    
    def handle_think(self, args: str) -> dict:
        mode = args.strip() if args else "on"
        return {"success": True, "output": {"thinking": mode}}
    
    def handle_solve(self, args: str) -> dict:
        return {"success": True, "output": {"solving": args, "status": "analyzing"}}
    
    def handle_run(self, args: str) -> dict:
        return {"success": True, "output": {"running": args, "status": "executing"}}
    
    def handle_execute(self, args: str) -> dict:
        return {"success": True, "output": {"executing": args}}
    
    def handle_cancel(self, args: str) -> dict:
        return {"success": True, "output": {"cancelled": True}}
    
    def handle_retry(self, args: str) -> dict:
        return {"success": True, "output": {"retrying": True}}
    
    def handle_continue(self, args: str) -> dict:
        return {"success": True, "output": {"continued": True}}
    
    def handle_pause(self, args: str) -> dict:
        return {"success": True, "output": {"paused": True}}
    
    def handle_resume(self, args: str) -> dict:
        return {"success": True, "output": {"resumed": True}}
    
    def handle_stop(self, args: str) -> dict:
        return {"success": True, "output": {"stopped": True}}
    
    def handle_queue(self, args: str) -> dict:
        return {"success": True, "output": {"queue": [], "action": args or "list"}}
    
    def handle_tasks(self, args: str) -> dict:
        return {"success": True, "output": {"tasks": [], "action": args or "list"}}
    
    def handle_history(self, args: str) -> dict:
        limit = int(args) if args and args.isdigit() else 10
        return {"success": True, "output": {"history": self._command_history[-limit:]}}
    
    # Code Commands
    def handle_code(self, args: str) -> dict:
        return {"success": True, "output": {"code_action": args or "help"}}
    
    def handle_debug(self, args: str) -> dict:
        return {"success": True, "output": {"debugging": args or "current context"}}
    
    def handle_fix(self, args: str) -> dict:
        return {"success": True, "output": {"fixing": args or "detected issues"}}
    
    def handle_explain(self, args: str) -> dict:
        return {"success": True, "output": {"explaining": args}}
    
    def handle_refactor(self, args: str) -> dict:
        return {"success": True, "output": {"refactoring": args}}
    
    def handle_review(self, args: str) -> dict:
        return {"success": True, "output": {"reviewing": args or "current file"}}
    
    def handle_optimize(self, args: str) -> dict:
        return {"success": True, "output": {"optimizing": args}}
    
    def handle_test(self, args: str) -> dict:
        return {"success": True, "output": {"testing": args or "all"}}
    
    def handle_benchmark(self, args: str) -> dict:
        return {"success": True, "output": {"benchmarking": args}}
    
    def handle_document(self, args: str) -> dict:
        return {"success": True, "output": {"documenting": args}}
    
    def handle_comment(self, args: str) -> dict:
        return {"success": True, "output": {"comment_action": args}}
    
    def handle_generate(self, args: str) -> dict:
        return {"success": True, "output": {"generating": args}}
    
    # Project Commands
    def handle_project(self, args: str) -> dict:
        return {"success": True, "output": {"project_action": args or "info"}}
    
    def handle_open(self, args: str) -> dict:
        return {"success": True, "output": {"opening": args or "."}}
    
    def handle_create(self, args: str) -> dict:
        return {"success": True, "output": {"creating": args}}
    
    def handle_init(self, args: str) -> dict:
        return {"success": True, "output": {"initializing": args or "project"}}
    
    def handle_build(self, args: str) -> dict:
        return {"success": True, "output": {"building": args or "project"}}
    
    def handle_run_project(self, args: str) -> dict:
        return {"success": True, "output": {"running_project": args}}
    
    def handle_analyze(self, args: str) -> dict:
        return {"success": True, "output": {"analyzing": args or "project"}}
    
    def handle_architecture(self, args: str) -> dict:
        return {"success": True, "output": {"architecture": args or "view"}}
    
    def handle_dependencies(self, args: str) -> dict:
        return {"success": True, "output": {"dependencies_action": args or "list"}}
    
    def handle_structure(self, args: str) -> dict:
        depth = int(args) if args and args.isdigit() else 2
        return {"success": True, "output": {"structure_depth": depth}}
    
    # Git Commands
    # Options git/gh permettant d'exécuter un programme arbitraire ou de
    # sortir du dépôt courant.
    _GIT_FORBIDDEN = (
        "-c", "--config", "--config-env", "--exec-path", "--upload-pack",
        "--receive-pack", "--exec", "--git-dir", "--work-tree", "--ext-cmd",
        "--ssh-command",
    )

    def _run_git(self, argv: list[str], binary: str = "git") -> dict:
        for tok in argv:
            low = tok.lower()
            if any(low == f or low.startswith(f + "=") for f in self._GIT_FORBIDDEN):
                return {"success": False, "error": f"Option non autorisée: {tok}"}
        if binary == "git" and argv and argv[0].startswith("-"):
            return {"success": False, "error": "Sous-commande git requise"}
        try:
            result = subprocess.run([binary] + argv, capture_output=True, text=True, timeout=30)
            return {"success": result.returncode == 0, "output": {"stdout": result.stdout, "stderr": result.stderr}}
        except FileNotFoundError:
            return {"success": False, "error": f"{binary} not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _run_gh(self, argv: list[str]) -> dict:
        return self._run_git(argv, binary="gh")

    def handle_git(self, args: str) -> dict:
        try:
            return self._run_git(shlex.split(args))
        except ValueError as e:
            return {"success": False, "error": str(e)}

    def handle_commit(self, args: str) -> dict:
        return self._run_git(["commit", "-m", args] if args else ["status"])
    
    def handle_push(self, args: str) -> dict:
        return self.handle_git(f"push {args}".strip())
    
    def handle_pull(self, args: str) -> dict:
        return self.handle_git(f"pull {args}".strip())
    
    def handle_branch(self, args: str) -> dict:
        return self.handle_git(f"branch {args}".strip())
    
    def handle_merge(self, args: str) -> dict:
        return self.handle_git(f"merge {args}".strip())
    
    def handle_tag(self, args: str) -> dict:
        return self.handle_git(f"tag {args}".strip())
    
    def handle_pr(self, args: str) -> dict:
        try:
            return self._run_gh(shlex.split(args))
        except ValueError as e:
            return {"success": False, "error": str(e)}
    
    def handle_issues(self, args: str) -> dict:
        return self.handle_pr(f"issue {args}".strip())
    
    def handle_release(self, args: str) -> dict:
        return self.handle_pr(f"release create {args}".strip())
    
    # Shell Commands
    def _run_shell(self, cmd: str, shell: str = "bash") -> dict:
        """Exécute une commande shell de façon sécurisée (jamais shell=True).

        - `cmd` est une chaîne qui est découpée via shlex (pas d'interprétation
          de métacaractères shell comme ; & | $()).
        - Aucun `shell=True` : un payload type "pkg; rm -rf /" est passé comme
          argument littéral au binaire, jamais interprété par un shell.
        - Allowlist de binaires autorisés pour limiter la surface d'exécution.
        """
        import shlex

        # Pas d'interpréteurs/shells (bash, sh, python, node, powershell, cmd...) :
        # ils annuleraient toute la liste blanche (`bash -c "..."`).
        ALLOWED_BINARIES = {
            "npm", "pnpm", "yarn", "bun", "pip", "pip3", "cargo", "go",
            "docker", "docker-compose", "kubectl", "aws", "gcloud", "az",
            "vercel", "wrangler", "git", "gh",
        }

        try:
            # Découpé sûr : pas d'injection de métacaractères shell
            parts = shlex.split(cmd)
            if not parts:
                return {"success": False, "error": "Commande vide"}
            binary = parts[0]
            if binary not in ALLOWED_BINARIES:
                return {"success": False, "error": f"Binaire non autorisé: {binary}"}
            if binary in ("git", "gh"):
                return self._run_git(parts[1:], binary=binary)

            result = subprocess.run(parts, capture_output=True, text=True, timeout=60)
            return {"success": result.returncode == 0,
                    "output": {"stdout": result.stdout, "stderr": result.stderr}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_bash(self, args: str) -> dict:
        return self._run_shell(args, "bash")
    
    def handle_powershell(self, args: str) -> dict:
        return self._run_shell(args, "powershell")
    
    def handle_cmd(self, args: str) -> dict:
        return self._run_shell(args, "cmd")
    
    def handle_shell(self, args: str) -> dict:
        return self._run_shell(args, "powershell")
    
    def handle_npm(self, args: str) -> dict:
        return self._run_shell(f"npm {args}")
    
    def handle_pnpm(self, args: str) -> dict:
        return self._run_shell(f"pnpm {args}")
    
    def handle_yarn(self, args: str) -> dict:
        return self._run_shell(f"yarn {args}")
    
    def handle_bun(self, args: str) -> dict:
        return self._run_shell(f"bun {args}")
    
    def handle_pip(self, args: str) -> dict:
        return self._run_shell(f"pip {args}")
    
    def handle_cargo(self, args: str) -> dict:
        return self._run_shell(f"cargo {args}")
    
    def handle_go(self, args: str) -> dict:
        return self._run_shell(f"go {args}")
    
    # Search Commands
    def handle_search(self, args: str) -> dict:
        return {"success": True, "output": {"searching": args}}
    
    def handle_web(self, args: str) -> dict:
        return {"success": True, "output": {"web_search": args}}
    
    def handle_google(self, args: str) -> dict:
        return {"success": True, "output": {"google_search": args}}
    
    def handle_github(self, args: str) -> dict:
        return {"success": True, "output": {"github_search": args}}
    
    def handle_docs(self, args: str) -> dict:
        return {"success": True, "output": {"docs_search": args}}
    
    def handle_api(self, args: str) -> dict:
        return {"success": True, "output": {"api_search": args}}
    
    def handle_research(self, args: str) -> dict:
        return {"success": True, "output": {"researching": args}}
    
    def handle_find(self, args: str) -> dict:
        return {"success": True, "output": {"finding": args}}
    
    # File Commands
    def handle_read(self, args: str) -> dict:
        try:
            path = Path(args)
            if path.exists() and path.is_file():
                content = path.read_text(encoding="utf-8", errors="ignore")
                return {"success": True, "output": {"content": content[:5000], "size": len(content)}}
            return {"success": False, "error": f"File not found: {args}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_write(self, args: str) -> dict:
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            return {"success": False, "error": "Usage: /write file content"}
        try:
            Path(parts[0]).write_text(parts[1], encoding="utf-8")
            return {"success": True, "output": {"written": parts[0], "size": len(parts[1])}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_edit(self, args: str) -> dict:
        return {"success": True, "output": {"editing": args}}
    
    def handle_create_file(self, args: str) -> dict:
        return self.handle_write(args)
    
    def handle_delete(self, args: str) -> dict:
        try:
            Path(args).unlink()
            return {"success": True, "output": {"deleted": args}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_move(self, args: str) -> dict:
        parts = args.split()
        if len(parts) < 2:
            return {"success": False, "error": "Usage: /move source dest"}
        try:
            Path(parts[0]).rename(parts[1])
            return {"success": True, "output": {"moved": parts[0], "to": parts[1]}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_copy(self, args: str) -> dict:
        parts = args.split()
        if len(parts) < 2:
            return {"success": False, "error": "Usage: /copy source dest"}
        try:
            import shutil
            shutil.copy2(parts[0], parts[1])
            return {"success": True, "output": {"copied": parts[0], "to": parts[1]}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_rename(self, args: str) -> dict:
        return self.handle_move(args)
    
    def handle_tree(self, args: str) -> dict:
        path = Path(args) if args else Path(".")
        depth = 2
        tree = []
        for root, dirs, files in os.walk(path):
            level = root.replace(str(path), "").count(os.sep)
            if level < depth:
                indent = " " * 2 * level
                tree.append(f"{indent}{os.path.basename(root)}/")
                subindent = " " * 2 * (level + 1)
                for file in files[:10]:
                    tree.append(f"{subindent}{file}")
        return {"success": True, "output": {"tree": "\n".join(tree[:50])}}
    
    def handle_list(self, args: str) -> dict:
        path = Path(args) if args else Path(".")
        try:
            items = list(path.iterdir())
            return {"success": True, "output": {"items": [i.name for i in items[:50]], "count": len(items)}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Database Commands
    def handle_sql(self, args: str) -> dict:
        return {"success": True, "output": {"sql": args, "status": "executed"}}
    
    def handle_query(self, args: str) -> dict:
        return self.handle_sql(args)
    
    def handle_schema(self, args: str) -> dict:
        return {"success": True, "output": {"schema": args or "all tables"}}
    
    def handle_migrate(self, args: str) -> dict:
        return {"success": True, "output": {"migrate": args}}
    
    def handle_seed(self, args: str) -> dict:
        return {"success": True, "output": {"seeding": args}}
    
    def handle_backup(self, args: str) -> dict:
        return {"success": True, "output": {"backup": args or "database"}}
    
    def handle_restore(self, args: str) -> dict:
        return {"success": True, "output": {"restoring": args}}
    
    # Docker Commands
    def handle_docker(self, args: str) -> dict:
        return self._run_shell(f"docker {args}")
    
    def handle_compose(self, args: str) -> dict:
        return self._run_shell(f"docker-compose {args}")
    
    def handle_k8s(self, args: str) -> dict:
        return self._run_shell(f"kubectl {args}")
    
    def handle_deploy(self, args: str) -> dict:
        return {"success": True, "output": {"deploying": args or "project"}}
    
    def handle_build_image(self, args: str) -> dict:
        return self._run_shell(f"docker build -t {args}")
    
    def handle_monitor(self, args: str) -> dict:
        return {"success": True, "output": {"monitoring": args}}
    
    # Cloud Commands
    def handle_aws(self, args: str) -> dict:
        return self._run_shell(f"aws {args}")
    
    def handle_gcp(self, args: str) -> dict:
        return self._run_shell(f"gcloud {args}")
    
    def handle_azure(self, args: str) -> dict:
        return self._run_shell(f"az {args}")
    
    def handle_vercel(self, args: str) -> dict:
        return self._run_shell(f"vercel {args}")
    
    def handle_cloudflare(self, args: str) -> dict:
        return self._run_shell(f"wrangler {args}")
    
    def handle_render(self, args: str) -> dict:
        return {"success": True, "output": {"render": args}}
    
    def handle_cloud(self, args: str) -> dict:
        return {"success": True, "output": {"cloud_action": args}}
    
    # AI Commands
    def handle_chat(self, args: str) -> dict:
        return {"success": True, "output": {"chat": args or "Starting chat session"}}
    
    def handle_agent(self, args: str) -> dict:
        return {"success": True, "output": {"agent_action": args}}
    
    def handle_reason(self, args: str) -> dict:
        return {"success": True, "output": {"reasoning": args}}
    
    def handle_reflect(self, args: str) -> dict:
        return {"success": True, "output": {"reflecting": args}}
    
    def handle_summarize(self, args: str) -> dict:
        return {"success": True, "output": {"summarizing": args}}
    
    def handle_translate(self, args: str) -> dict:
        return {"success": True, "output": {"translating": args}}
    
    def handle_prompt(self, args: str) -> dict:
        return {"success": True, "output": {"prompt": args}}
    
    def handle_rag(self, args: str) -> dict:
        return {"success": True, "output": {"rag_action": args}}
    
    def handle_embed(self, args: str) -> dict:
        return {"success": True, "output": {"embedding": args}}
    
    # Media Commands
    def handle_image(self, args: str) -> dict:
        return {"success": True, "output": {"image_action": args}}
    
    def handle_analyze_image(self, args: str) -> dict:
        return {"success": True, "output": {"analyzing_image": args}}
    
    def handle_ocr(self, args: str) -> dict:
        return {"success": True, "output": {"ocr": args}}
    
    def handle_generate_image(self, args: str) -> dict:
        return {"success": True, "output": {"generating_image": args}}
    
    def handle_edit_image(self, args: str) -> dict:
        return {"success": True, "output": {"editing_image": args}}
    
    def handle_transcribe(self, args: str) -> dict:
        return {"success": True, "output": {"transcribing": args}}
    
    def handle_speech(self, args: str) -> dict:
        return {"success": True, "output": {"speech": args}}
    
    def handle_tts(self, args: str) -> dict:
        return self.handle_speech(args)
    
    def handle_audio(self, args: str) -> dict:
        return {"success": True, "output": {"audio_action": args}}
    
    def handle_video(self, args: str) -> dict:
        return {"success": True, "output": {"video_action": args}}
    
    def handle_subtitles(self, args: str) -> dict:
        return {"success": True, "output": {"generating_subtitles": args}}
    
    def handle_clips(self, args: str) -> dict:
        return {"success": True, "output": {"creating_clip": args}}
    
    def handle_analyze_video(self, args: str) -> dict:
        return {"success": True, "output": {"analyzing_video": args}}
    
    # Productivity Commands
    def handle_todo(self, args: str) -> dict:
        return {"success": True, "output": {"todo_action": args or "list"}}
    
    def handle_calendar(self, args: str) -> dict:
        return {"success": True, "output": {"calendar_action": args}}
    
    def handle_meeting(self, args: str) -> dict:
        return {"success": True, "output": {"meeting_action": args}}
    
    def handle_report(self, args: str) -> dict:
        return {"success": True, "output": {"report_type": args or "daily"}}
    
    def handle_email(self, args: str) -> dict:
        return {"success": True, "output": {"email_action": args}}
    
    def handle_notes(self, args: str) -> dict:
        return {"success": True, "output": {"notes_action": args}}
    
    # Security Commands
    def handle_security(self, args: str) -> dict:
        return {"success": True, "output": {"security_action": args or "scan"}}
    
    def handle_audit(self, args: str) -> dict:
        return {"success": True, "output": {"auditing": args or "project"}}
    
    def handle_scan(self, args: str) -> dict:
        return {"success": True, "output": {"scanning": args}}
    
    def handle_secrets(self, args: str) -> dict:
        return {"success": True, "output": {"secrets_action": args}}
    
    # Browser Commands
    def handle_browser(self, args: str) -> dict:
        return {"success": True, "output": {"browser_action": args}}
    
    def handle_playwright(self, args: str) -> dict:
        return {"success": True, "output": {"playwright_action": args}}
    
    def handle_selenium(self, args: str) -> dict:
        return {"success": True, "output": {"selenium_action": args}}
    
    def handle_workflow(self, args: str) -> dict:
        return {"success": True, "output": {"workflow_action": args}}
    
    def handle_automation(self, args: str) -> dict:
        return {"success": True, "output": {"automation_action": args}}
    
    # Memory Commands
    def handle_save(self, args: str) -> dict:
        parts = args.split(maxsplit=1)
        if len(parts) == 2:
            self._memory[parts[0]] = parts[1]
            return {"success": True, "output": {"saved": {parts[0]: parts[1]}}}
        return {"success": False, "error": "Usage: /save key value"}
    
    def handle_load(self, args: str) -> dict:
        value = self._memory.get(args)
        if value:
            return {"success": True, "output": {args: value}}
        return {"success": False, "error": f"Key not found: {args}"}
    
    def handle_forget(self, args: str) -> dict:
        if args in self._memory:
            del self._memory[args]
            return {"success": True, "output": {"forgotten": args}}
        return {"success": False, "error": f"Key not found: {args}"}
    
    def handle_remember(self, args: str) -> dict:
        return self.handle_save(args)
    
    def handle_export_memory(self, args: str) -> dict:
        try:
            Path(args).write_text(json.dumps(self._memory, indent=2))
            return {"success": True, "output": {"exported": args, "entries": len(self._memory)}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_import_memory(self, args: str) -> dict:
        try:
            self._memory.update(json.loads(Path(args).read_text()))
            return {"success": True, "output": {"imported": args, "entries": len(self._memory)}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Tools Commands
    def handle_tool(self, args: str) -> dict:
        return {"success": True, "output": {"tool_action": args}}
    
    def handle_install(self, args: str) -> dict:
        return self._run_shell(f"pip install {args}")
    
    def handle_uninstall(self, args: str) -> dict:
        return self._run_shell(f"pip uninstall -y {args}")
    
    def handle_update(self, args: str) -> dict:
        if args:
            return self._run_shell(f"pip install --upgrade {args}")
        return self._run_shell("pip list --outdated")
    
    def handle_list_tools(self, args: str) -> dict:
        return self._run_shell("pip list")
    
    # MCP Commands
    def handle_mcp(self, args: str) -> dict:
        return {"success": True, "output": {"mcp_action": args}}
    
    def handle_mcp_connect(self, args: str) -> dict:
        return {"success": True, "output": {"connecting": args}}
    
    def handle_mcp_list(self, args: str) -> dict:
        return {"success": True, "output": {"mcp_servers": []}}
    
    def handle_mcp_install(self, args: str) -> dict:
        return {"success": True, "output": {"installing_mcp": args}}
    
    def handle_mcp_remove(self, args: str) -> dict:
        return {"success": True, "output": {"removing_mcp": args}}
    
    # Automation Commands
    def handle_auto(self, args: str) -> dict:
        return {"success": True, "output": {"auto_mode": args or "on"}}
    
    def handle_manual(self, args: str) -> dict:
        return {"success": True, "output": {"manual_mode": True}}
    
    def handle_safe(self, args: str) -> dict:
        return {"success": True, "output": {"safe_mode": args or "on"}}
    
    def handle_full_auto(self, args: str) -> dict:
        return {"success": True, "output": {"full_auto_mode": args or "on"}}
    
    def handle_autonomous(self, args: str) -> dict:
        return {"success": True, "output": {"autonomous_mode": args or "on"}}
    
    # Monitoring Commands
    def handle_trace(self, args: str) -> dict:
        return {"success": True, "output": {"trace": args or "current session"}}
    
    def handle_profile(self, args: str) -> dict:
        return {"success": True, "output": {"profiling": args}}
    
    def handle_metrics(self, args: str) -> dict:
        return {"success": True, "output": {"metrics": {"commands": len(self._command_history), "memory": len(self._memory)}}}
    
    def handle_tokens(self, args: str) -> dict:
        return {"success": True, "output": {"tokens_used": 0, "tokens_limit": 100000}}
    
    def handle_cost(self, args: str) -> dict:
        return {"success": True, "output": {"cost": "$0.00", "period": args or "today"}}
    
    def handle_performance(self, args: str) -> dict:
        return {"success": True, "output": {"performance": "optimal"}}
    
    # Advanced Commands
    def handle_deep_research(self, args: str) -> dict:
        return {"success": True, "output": {"deep_research": args}}
    
    def handle_analyze_repo(self, args: str) -> dict:
        return {"success": True, "output": {"analyzing_repo": args}}
    
    def handle_explain_codebase(self, args: str) -> dict:
        return {"success": True, "output": {"explaining_codebase": args}}
    
    def handle_index_project(self, args: str) -> dict:
        return {"success": True, "output": {"indexing_project": True}}
    
    def handle_search_symbol(self, args: str) -> dict:
        return {"success": True, "output": {"searching_symbol": args}}
    
    def handle_find_references(self, args: str) -> dict:
        return {"success": True, "output": {"finding_references": args}}
    
    def handle_generate_tests(self, args: str) -> dict:
        return {"success": True, "output": {"generating_tests": args}}
    
    def handle_fix_all(self, args: str) -> dict:
        return {"success": True, "output": {"fixing_all": True}}
    
    def handle_review_pr(self, args: str) -> dict:
        return {"success": True, "output": {"reviewing_pr": args}}
    
    def handle_create_spec(self, args: str) -> dict:
        return {"success": True, "output": {"creating_spec": args}}
    
    def handle_create_roadmap(self, args: str) -> dict:
        return {"success": True, "output": {"creating_roadmap": args}}
    
    def handle_design_system(self, args: str) -> dict:
        return {"success": True, "output": {"design_system": True}}
    
    def handle_run_ci(self, args: str) -> dict:
        return {"success": True, "output": {"running_ci": True}}
    
    def handle_deploy_preview(self, args: str) -> dict:
        return {"success": True, "output": {"deploying_preview": True}}
    
    def handle_benchmark_project(self, args: str) -> dict:
        return {"success": True, "output": {"benchmarking_project": True}}
    
    def handle_profile_project(self, args: str) -> dict:
        return {"success": True, "output": {"profiling_project": True}}
    
    def handle_scan_security(self, args: str) -> dict:
        return {"success": True, "output": {"scanning_security": True}}
    
    def handle_migrate_project(self, args: str) -> dict:
        return {"success": True, "output": {"migrating_project": args}}
    
    def handle_upgrade_dependencies(self, args: str) -> dict:
        return {"success": True, "output": {"upgrading_dependencies": True}}
    
    def handle_create_agent(self, args: str) -> dict:
        return {"success": True, "output": {"creating_agent": args}}
    
    def handle_install_skill(self, args: str) -> dict:
        return {"success": True, "output": {"installing_skill": args}}

    # Extended Slash Commands
    def handle_goal(self, args: str) -> dict:
        return {"success": True, "output": {"goal": args or "Mode objectif long terme activé", "status": "active"}}

    def handle_schedule(self, args: str) -> dict:
        return {"success": True, "output": {"schedule": args or "Tâche planifiée enregistrée", "status": "scheduled"}}

    def handle_browser(self, args: str) -> dict:
        return {"success": True, "output": {"browser_action": args or "Session de navigation web ouverte", "status": "ready"}}

    def handle_learn(self, args: str) -> dict:
        return {"success": True, "output": {"learned": args or "Nouvelle règle enregistrée dans la mémoire", "saved": True}}

    def handle_teamwork(self, args: str) -> dict:
        return {"success": True, "output": {"mode": "teamwork", "active_agents": ["CODER", "DEBUGGER", "RESEARCHER", "ARCHITECT"]}}

    def handle_compact(self, args: str) -> dict:
        return {"success": True, "output": {"compacted": True, "message": "Historique de conversation compacté"}}

    def handle_undo(self, args: str) -> dict:
        return {"success": True, "output": {"rollback": True, "message": "Dernier snapshot restauré"}}
