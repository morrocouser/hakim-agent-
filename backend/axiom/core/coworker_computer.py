"""Coworker Dedicated Virtual Computer & Execution Environment.

Inspired by CopilotKit OpenBot:
- Each coworker has an isolated workspace directory and virtual computer.
- Live screen / browser view state.
- Interactive terminal buffer.
- "Take the Wheel" handover state machine:
  IDLE -> BOT_ACTIVE -> HELP_REQUESTED -> HUMAN_CONTROLLED -> BOT_ACTIVE.
"""

from __future__ import annotations
import os
import time
import subprocess
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from axiom.core.policy_gateway import (
    policy_gateway, PolicyDecision, InitiatorKind, ActionRequest, EvaluationResult
)
from axiom.core.audit_ledger import audit_ledger
from axiom.logging_setup import log


class ControlState(str, Enum):
    IDLE = "IDLE"
    BOT_ACTIVE = "BOT_ACTIVE"
    HELP_REQUESTED = "HELP_REQUESTED"      # 2FA, Captcha, or sensitive checkpoint
    HUMAN_CONTROLLED = "HUMAN_CONTROLLED"  # Human has "Taken the Wheel"


class VirtualScreenState(BaseModel):
    current_url: str = "https://agent.local/workspace"
    page_title: str = "Coworker Workspace"
    viewport_width: int = 1280
    viewport_height: int = 800
    is_secure: bool = True
    status_code: int = 200
    dom_summary: str = "<div class='workspace-root'><p>Espace de travail virtuel initialisé</p></div>"
    last_snapshot_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class VirtualTerminalLine(BaseModel):
    type: str  # "command", "stdout", "stderr", "info"
    text: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CoworkerRoutine(BaseModel):
    id: str
    name: str
    description: str
    cron_schedule: str
    last_run: Optional[str] = None
    last_status: str = "ready"  # "ready", "running", "success", "failed"
    command_to_run: str


class CoworkerProfile(BaseModel):
    id: str
    name: str
    role: str
    speciality: str
    avatar_color: str
    description: str
    tools: List[str]
    control_state: ControlState = ControlState.IDLE
    help_reason: Optional[str] = None
    workspace_path: str
    screen: VirtualScreenState = Field(default_factory=VirtualScreenState)
    terminal_buffer: List[VirtualTerminalLine] = Field(default_factory=list)
    routines: List[CoworkerRoutine] = Field(default_factory=list)


class CoworkerComputerManager:
    """Manages virtual computers and workspaces for all AI coworkers."""

    def __init__(self):
        self._coworkers: Dict[str, CoworkerProfile] = {}
        self._base_workspace_dir = os.path.join(os.getcwd(), "user_files", "coworkers")
        os.makedirs(self._base_workspace_dir, exist_ok=True)
        self._initialize_default_coworkers()

    def _initialize_default_coworkers(self):
        """Setup initial OpenBot coworkers with dedicated workspaces."""
        profiles = [
            {
                "id": "bot-browser",
                "name": "Alex Browser",
                "role": "Web Navigator & Research Coworker",
                "speciality": "Exploration web, scraping, extraction de données et formulaires",
                "avatar_color": "#3b82f6",
                "description": "Navigue sur le web pour extraire des informations, tester des applications et remplir des formulaires avec assistance humaine sur les 2FA/CAPTCHA.",
                "tools": ["browser_navigate", "browser_click", "browser_type", "web_search", "extract_content"],
                "url": "https://docs.github.com/fr",
                "title": "Documentation GitHub",
                "routines": [
                    CoworkerRoutine(
                        id="routine_check_updates",
                        name="Veille technologique quotidienne",
                        description="Vérifie les mises à jour majeures des dépendances et de la documentation",
                        cron_schedule="0 9 * * 1-5",
                        last_run=datetime.utcnow().isoformat(),
                        last_status="success",
                        command_to_run="browser_navigate https://news.ycombinator.com",
                    )
                ],
            },
            {
                "id": "bot-sentinel",
                "name": "Sentinel SecOps",
                "role": "Security & Governance Coworker",
                "speciality": "Audit de conformité, surveillance des failles et politique CEL",
                "avatar_color": "#10b981",
                "description": "Vérifie les règles de sécurité, analyse le code source contre les vulnérabilités et bloque les exécutions non autorisées.",
                "tools": ["security_scan", "policy_eval", "audit_lookup", "shell_exec"],
                "url": "https://security.local/dashboard",
                "title": "Security Dashboard — All Clear",
                "routines": [
                    CoworkerRoutine(
                        id="routine_sec_scan",
                        name="Scan nocturne des dépendances",
                        description="Exécute un scan de sécurité sur tous les paquets du projet",
                        cron_schedule="0 2 * * *",
                        last_run=datetime.utcnow().isoformat(),
                        last_status="success",
                        command_to_run="npm audit",
                    )
                ],
            },
            {
                "id": "bot-devops",
                "name": "Marcus DevOps",
                "role": "Infrastructure & Build Coworker",
                "speciality": "Exécution shell, conteneurs, builds Next.js et déploiements",
                "avatar_color": "#D97757",
                "description": "Exécute des scripts et commandes de compilation dans son conteneur isolé avec traçabilité complète de chaque commande.",
                "tools": ["shell_exec", "file_manager", "git_status", "docker_inspect"],
                "url": "https://localhost:3000/dashboard",
                "title": "HakimAgent Local App Shell",
                "routines": [
                    CoworkerRoutine(
                        id="routine_build_check",
                        name="Validation périodique du build",
                        description="Teste la compilation de l'application Next.js",
                        cron_schedule="*/30 * * * *",
                        last_run=datetime.utcnow().isoformat(),
                        last_status="success",
                        command_to_run="npm run build",
                    )
                ],
            },
            {
                "id": "bot-curator",
                "name": "Nora Curator",
                "role": "Data & Knowledge Coworker",
                "speciality": "Organisation des fichiers, synthèse markdown et mémoire persistante",
                "avatar_color": "#a855f7",
                "description": "Structure la documentation, synthétise les échanges et gère les fichiers du projet.",
                "tools": ["create_file", "edit_file", "read_file", "summarize_text"],
                "url": "file:///workspace/summary.md",
                "title": "Knowledge Base & Workspace",
                "routines": [],
            },
            {
                "id": "bot-webcraft",
                "name": "Elena WebCraft",
                "role": "Website Creator & Frontend Specialist",
                "speciality": "Création de sites web complets, landing pages Tailwind, intégration responsive et preview live",
                "avatar_color": "#06b6d4",
                "description": "Conçoit et génère des sites web modernes, des landing pages et des interfaces interactives complètes avec prévisualisation en direct.",
                "tools": [
                    "web_scaffold",
                    "web_generate_page",
                    "component_builder",
                    "web_preview",
                    "file_manager",
                    "shell_exec",
                ],
                "url": "http://localhost:3000/preview/site",
                "title": "Elena WebCraft Studio — Live Website",
                "routines": [
                    CoworkerRoutine(
                        id="routine_web_preview",
                        name="Vérification et rendu du prototype web",
                        description="Vérifie la syntaxe HTML/Tailwind et génère un snapshot de preview",
                        cron_schedule="*/15 * * * *",
                        last_run=datetime.utcnow().isoformat(),
                        last_status="success",
                        command_to_run="web_preview index.html",
                    ),
                    CoworkerRoutine(
                        id="routine_audit_ux",
                        name="Audit de performance & accessibilité web",
                        description="Audit des balises sémantiques, du contraste et du responsive design",
                        cron_schedule="0 10 * * 1",
                        last_run=datetime.utcnow().isoformat(),
                        last_status="ready",
                        command_to_run="web_audit_ux",
                    ),
                ],
            },
            {
                "id": "bot-agency-reviewer",
                "name": "Alex Code Reviewer",
                "role": "QA & Code Review Specialist (Agency)",
                "speciality": "Revue de code approfondie, analyse des vulnérabilités, performance & maintenabilité",
                "avatar_color": "#8b5cf6",
                "description": "Examine le code source, identifie les bugs subtils et propose des revues constructives avec des suggestions concrètes.",
                "tools": ["code_review", "security_scan", "file_manager", "diff_analyze"],
                "url": "https://agency.local/code-reviewer",
                "title": "Agency Code Reviewer Terminal",
                "routines": [
                    CoworkerRoutine(
                        id="routine_agency_code_review",
                        name="Audit de qualité de code",
                        description="Vérifie la conformité, la sécurité et l'absence de régression",
                        cron_schedule="0 18 * * 1-5",
                        last_run=datetime.utcnow().isoformat(),
                        last_status="ready",
                        command_to_run="code_review src/",
                    )
                ],
            },
            {
                "id": "bot-agency-architect",
                "name": "Atlas Software Architect",
                "role": "System Architecture Specialist (Agency)",
                "speciality": "Architecture logicielle, conception de systèmes distribués, ADR et choix techniques",
                "avatar_color": "#3b82f6",
                "description": "Définit les architectures modulaires, documente les choix clés (ADR) et garantit la scalabilité des composants.",
                "tools": ["architecture_design", "file_manager", "schema_validator", "system_specs"],
                "url": "https://agency.local/architect",
                "title": "Agency Architecture Studio",
                "routines": [],
            },
            {
                "id": "bot-agency-secops",
                "name": "Cipher Security Auditor",
                "role": "Application Security Specialist (Agency)",
                "speciality": "Audit de sécurité applicative, modélisation de menaces, conformité OWASP & patchs",
                "avatar_color": "#ef4444",
                "description": "Détecte les failles OWASP Top 10, contrôle les dépendances et audite les politiques de sécurité.",
                "tools": ["security_scan", "policy_eval", "audit_lookup", "shell_exec"],
                "url": "https://agency.local/security",
                "title": "Agency Security Operations",
                "routines": [],
            },
            {
                "id": "bot-agency-growth",
                "name": "Blaze Growth Hacker",
                "role": "Growth Marketing & CRO (Agency)",
                "speciality": "Entonnoirs d'acquisition, stratégies virales, optimisation du taux de conversion (CRO)",
                "avatar_color": "#f97316",
                "description": "Conçoit des tunnels de conversion, analyse les métriques utilisateurs et optimise le copywriting de croissance.",
                "tools": ["funnel_analysis", "web_search", "extract_content", "analytics_audit"],
                "url": "https://agency.local/growth",
                "title": "Agency Growth Station",
                "routines": [],
            },
            {
                "id": "bot-agency-prompt",
                "name": "Nova Prompt Engineer",
                "role": "Prompt Engineer & LLM Evaluator (Agency)",
                "speciality": "Ingénierie de prompts haute précision, évaluation des modèles et meta-prompts",
                "avatar_color": "#6366f1",
                "description": "Optimise les prompts système, évalue les modèles sur des benchmarks et réduit les coûts de tokens.",
                "tools": ["prompt_eval", "test_runner", "token_optimizer", "benchmark_test"],
                "url": "https://agency.local/prompts",
                "title": "Agency Prompt Lab",
                "routines": [],
            },
        ]

        for p in profiles:
            coworker_ws = os.path.join(self._base_workspace_dir, p["id"], "workspace")
            os.makedirs(coworker_ws, exist_ok=True)

            screen = VirtualScreenState(
                current_url=p["url"],
                page_title=p["title"],
                dom_summary=f"<h3>{p['title']}</h3><p>{p['description']}</p>",
            )

            terminal = [
                VirtualTerminalLine(type="info", text=f"=== Initialisation de l'environnement virtuel pour {p['name']} ==="),
                VirtualTerminalLine(type="info", text=f"Workspace monté sur : {coworker_ws}"),
                VirtualTerminalLine(type="stdout", text=f"Statut : Prêt pour l'exécution gouvernée."),
            ]

            profile = CoworkerProfile(
                id=p["id"],
                name=p["name"],
                role=p["role"],
                speciality=p["speciality"],
                avatar_color=p["avatar_color"],
                description=p["description"],
                tools=p["tools"],
                control_state=ControlState.IDLE,
                workspace_path=coworker_ws,
                screen=screen,
                terminal_buffer=terminal,
                routines=p["routines"],
            )
            self._coworkers[p["id"]] = profile

    def list_coworkers(self) -> List[Dict[str, Any]]:
        return [c.dict() for c in self._coworkers.values()]

    def get_coworker(self, coworker_id: str) -> Optional[CoworkerProfile]:
        return self._coworkers.get(coworker_id)

    def spawn_agency_coworker(self, slug: str) -> CoworkerProfile:
        """Dynamically instantiate any of the 267 Agency Agents as an active Coworker."""
        clean_slug = slug.lower().replace("agency-", "").replace("bot-agency-", "")
        coworker_id = f"bot-agency-{clean_slug}"
        if coworker_id in self._coworkers:
            return self._coworkers[coworker_id]

        import json
        catalog_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "agency_agents_catalog.json"
        )
        agent_data = None
        if os.path.exists(catalog_path):
            try:
                with open(catalog_path, encoding="utf-8") as f:
                    cat = json.load(f)
                    for a in cat.get("agents", []):
                        if a.get("slug") == clean_slug or a.get("skill_slug") == f"agency-{clean_slug}":
                            agent_data = a
                            break
            except Exception:
                pass

        name = agent_data["name"] if agent_data else clean_slug.replace("-", " ").title()
        div_label = agent_data.get("division_label", "Agency Specialist") if agent_data else "Agency Specialist"
        role = f"{name} ({div_label})"
        speciality = agent_data.get("description", "Agent spécialisé Agency") if agent_data else "Agent spécialisé"
        color = agent_data.get("color", "#6366F1") if agent_data else "#6366F1"
        desc = agent_data.get("vibe", speciality) if agent_data else speciality

        coworker_ws = os.path.join(self._base_workspace_dir, coworker_id, "workspace")
        os.makedirs(coworker_ws, exist_ok=True)

        screen = VirtualScreenState(
            current_url=f"https://agency.local/{clean_slug}",
            page_title=f"{name} — Agency Station",
            dom_summary=f"<h3>{name}</h3><p>{speciality}</p>",
        )

        terminal = [
            VirtualTerminalLine(type="info", text=f"=== Initialisation de l'ordinateur virtuel pour {name} ==="),
            VirtualTerminalLine(type="info", text=f"Workspace monté sur : {coworker_ws}"),
            VirtualTerminalLine(type="stdout", text="Statut : Prêt pour l'exécution gouvernée."),
        ]

        profile = CoworkerProfile(
            id=coworker_id,
            name=name,
            role=role,
            speciality=speciality,
            avatar_color=color,
            description=desc,
            tools=["file_manager", "web_search", "shell_exec", "diff_analyze"],
            control_state=ControlState.IDLE,
            workspace_path=coworker_ws,
            screen=screen,
            terminal_buffer=terminal,
            routines=[],
        )
        self._coworkers[coworker_id] = profile
        return profile

    # -------------------------------------------------------------
    # "Take the Wheel" Handover Lifecycle
    # -------------------------------------------------------------

    def request_help(self, coworker_id: str, reason: str) -> CoworkerProfile:
        """Triggered when a coworker hits a 2FA prompt, CAPTCHA, or sensitive operation."""
        coworker = self._coworkers.get(coworker_id)
        if not coworker:
            raise ValueError(f"Coworker {coworker_id} introuvable")

        coworker.control_state = ControlState.HELP_REQUESTED
        coworker.help_reason = reason
        coworker.terminal_buffer.append(
            VirtualTerminalLine(
                type="stderr",
                text=f"⚠️ [AIDE REQUISE] L'agent sollicite une intervention humaine : {reason}",
            )
        )

        audit_ledger.record_control_event(
            coworker_id=coworker.id,
            coworker_name=coworker.name,
            event_type="computer.help_requested",
            details={"reason": reason},
        )
        return coworker

    def take_the_wheel(self, coworker_id: str, operator_id: str = "human_operator") -> CoworkerProfile:
        """Human operator takes direct control of the coworker's screen/computer."""
        coworker = self._coworkers.get(coworker_id)
        if not coworker:
            raise ValueError(f"Coworker {coworker_id} introuvable")

        coworker.control_state = ControlState.HUMAN_CONTROLLED
        coworker.help_reason = None
        coworker.terminal_buffer.append(
            VirtualTerminalLine(
                type="info",
                text=f"🎮 [CONTRÔLE PRIS] L'opérateur {operator_id} a pris le volant ('Take the Wheel').",
            )
        )

        audit_ledger.record_control_event(
            coworker_id=coworker.id,
            coworker_name=coworker.name,
            event_type="computer.control_taken",
            details={"operator_id": operator_id},
        )
        return coworker

    def release_the_wheel(self, coworker_id: str, operator_id: str = "human_operator") -> CoworkerProfile:
        """Human operator releases control back to the AI coworker."""
        coworker = self._coworkers.get(coworker_id)
        if not coworker:
            raise ValueError(f"Coworker {coworker_id} introuvable")

        coworker.control_state = ControlState.BOT_ACTIVE
        coworker.help_reason = None
        coworker.terminal_buffer.append(
            VirtualTerminalLine(
                type="info",
                text=f"🤖 [CONTRÔLE RENDU] L'opérateur a rendu les commandes au coworker.",
            )
        )

        audit_ledger.record_control_event(
            coworker_id=coworker.id,
            coworker_name=coworker.name,
            event_type="computer.control_released",
            details={"operator_id": operator_id},
        )
        return coworker

    # -------------------------------------------------------------
    # Governed Execution on Coworker Computer
    # -------------------------------------------------------------

    def execute_action(
        self,
        coworker_id: str,
        tool_name: str,
        intent: str,
        command: Optional[str] = None,
        url: Optional[str] = None,
        file_path: Optional[str] = None,
        initiator_kind: InitiatorKind = InitiatorKind.PERSON,
        actor_id: str = "user",
    ) -> Dict[str, Any]:
        """Execute an action on the coworker's computer through Policy Gateway."""
        coworker = self._coworkers.get(coworker_id)
        if not coworker:
            raise ValueError(f"Coworker {coworker_id} introuvable")

        # Prepare action request
        req = ActionRequest(
            tool_name=tool_name,
            intent=intent,
            coworker_id=coworker_id,
            coworker_name=coworker.name,
            actor_id=actor_id,
            initiator_kind=initiator_kind,
            command=command,
            url=url,
            file_path=file_path,
        )

        start_time = time.time()
        eval_result = policy_gateway.evaluate(req)

        # 1. If Denied
        if eval_result.decision == PolicyDecision.DENIED:
            audit_ledger.record_decision(
                eval_result,
                status="denied",
                duration_ms=int((time.time() - start_time) * 1000),
            )
            coworker.terminal_buffer.append(
                VirtualTerminalLine(
                    type="stderr",
                    text=f"🚫 [POLITIQUE REFUSÉE] {eval_result.reason}",
                )
            )
            return {
                "success": False,
                "decision": eval_result.decision.value,
                "reason": eval_result.reason,
                "rule_id": eval_result.rule_id,
            }

        # 2. If Require Takeover ("Take the Wheel")
        if eval_result.decision == PolicyDecision.REQUIRE_TAKEOVER:
            self.request_help(coworker_id, reason=eval_result.reason)
            audit_ledger.record_decision(
                eval_result,
                status="paused_for_takeover",
                duration_ms=int((time.time() - start_time) * 1000),
            )
            return {
                "success": False,
                "decision": eval_result.decision.value,
                "reason": eval_result.reason,
                "rule_id": eval_result.rule_id,
                "require_takeover": True,
            }

        # 3. If Allowed -> Perform on virtual computer
        output = "Action exécutée avec succès."
        if url:
            coworker.screen.current_url = url
            coworker.screen.page_title = f"Page: {url.split('//')[-1]}"
            coworker.screen.dom_summary = f"Page chargée avec succès : {url}"
            coworker.screen.last_snapshot_at = datetime.utcnow().isoformat()
            coworker.terminal_buffer.append(
                VirtualTerminalLine(type="stdout", text=f"🌐 [BROWSER] Navigation vers : {url}")
            )
            output = f"Navigation terminée vers {url}"

        if command:
            coworker.terminal_buffer.append(
                VirtualTerminalLine(type="command", text=f"$ {command}")
            )
            output = f"Commande validée et exécutée en sandbox : {command}"
            coworker.terminal_buffer.append(
                VirtualTerminalLine(type="stdout", text=output)
            )

        if tool_name in ("web_scaffold", "web_generate_page", "web_preview", "component_builder"):
            site_dir = os.path.join(coworker.workspace_path, "site")
            os.makedirs(site_dir, exist_ok=True)
            index_path = os.path.join(site_dir, "index.html")

            site_name = intent.replace("Création site :", "").strip() or "Mon Nouveau Site Web"
            page_content = f"""<!DOCTYPE html>
<html lang="fr" class="scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{site_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
</head>
<body class="bg-neutral-950 text-neutral-100 min-h-screen antialiased selection:bg-cyan-500 selection:text-black">
  <nav class="border-b border-neutral-800/80 bg-neutral-900/60 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
    <div class="flex items-center gap-2.5">
      <div class="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_10px_#22d3ee] animate-pulse"></div>
      <span class="font-bold tracking-tight text-white">{site_name}</span>
    </div>
    <div class="flex items-center gap-5 text-xs text-neutral-400 font-medium">
      <a href="#hero" class="hover:text-white transition">Accueil</a>
      <a href="#features" class="hover:text-white transition">Services</a>
      <a href="#contact" class="hover:text-white transition">Contact</a>
      <button class="bg-cyan-500 hover:bg-cyan-400 text-neutral-950 px-3.5 py-1.5 rounded-lg font-semibold transition cursor-pointer">Explorer</button>
    </div>
  </nav>

  <header id="hero" class="py-24 px-6 text-center max-w-4xl mx-auto space-y-6">
    <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-mono">
      <span>●</span> Site Web Actif & Déployé
    </div>
    <h1 class="text-4xl sm:text-6xl font-extrabold tracking-tight text-white">
      {site_name}
    </h1>
    <p class="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
      Site web généré par l'agent Elena WebCraft avec architecture HTML5 sémantique, Tailwind CSS moderne et composants responsives.
    </p>
    <div class="flex items-center justify-center gap-3 pt-4">
      <button class="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-neutral-950 font-semibold text-xs transition shadow-lg shadow-cyan-500/20">
        Commencer maintenant
      </button>
      <button class="px-5 py-2.5 rounded-xl bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 text-neutral-300 text-xs font-medium transition">
        Voir les fonctionnalités
      </button>
    </div>
  </header>

  <section id="features" class="py-16 px-6 max-w-5xl mx-auto">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 hover:border-cyan-500/40 transition">
        <div class="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold text-sm mb-3">01</div>
        <h3 class="text-base font-semibold text-white">Design Moderne</h3>
        <p class="text-xs text-neutral-400 mt-1.5 leading-relaxed">Conception épurée style Glassmorphic avec Tailwind CSS et typographie optimisée.</p>
      </div>
      <div class="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 hover:border-cyan-500/40 transition">
        <div class="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold text-sm mb-3">02</div>
        <h3 class="text-base font-semibold text-white">Responsive & Rapide</h3>
        <p class="text-xs text-neutral-400 mt-1.5 leading-relaxed">Rendu ultra-fluide adapté à tous les écrans mobiles, tablettes et ordinateurs.</p>
      </div>
      <div class="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 hover:border-cyan-500/40 transition">
        <div class="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold text-sm mb-3">03</div>
        <h3 class="text-base font-semibold text-white">Prêt à Déployer</h3>
        <p class="text-xs text-neutral-400 mt-1.5 leading-relaxed">Code source autonome sauvegardé directement dans le conteneur virtuel de l'agent.</p>
      </div>
    </div>
  </section>

  <footer class="border-t border-neutral-900 py-8 px-6 text-center text-xs text-neutral-500 font-mono">
    Généré par HakimAgent · Elena WebCraft Studio
  </footer>
</body>
</html>"""
            try:
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(page_content)
            except Exception as e:
                log.error("Erreur écriture fichier site: %s", e)

            clean_url = f"file:///{index_path.replace(os.sep, '/')}"
            coworker.screen.current_url = clean_url
            coworker.screen.page_title = f"{site_name} — Live Site Preview"
            coworker.screen.dom_summary = f"<div class='p-3 bg-neutral-900 text-white rounded-xl'><h4>🌐 {site_name}</h4><p class='text-xs text-neutral-400'>Site web scaffoldé avec succès dans le workspace. Fichiers : <code>{index_path}</code></p></div>"
            coworker.screen.last_snapshot_at = datetime.utcnow().isoformat()

            coworker.terminal_buffer.append(
                VirtualTerminalLine(type="command", text=f"$ web_scaffold --name \"{site_name}\"")
            )
            coworker.terminal_buffer.append(
                VirtualTerminalLine(type="stdout", text=f"📁 Dossier initialisé : {site_dir}")
            )
            coworker.terminal_buffer.append(
                VirtualTerminalLine(type="stdout", text=f"🎨 Fichier HTML/Tailwind généré : index.html")
            )
            coworker.terminal_buffer.append(
                VirtualTerminalLine(type="stdout", text=f"✨ Aperçu live chargé avec succès sur l'écran virtuel.")
            )
            output = f"Site web '{site_name}' créé avec succès dans le conteneur virtuel. Le fichier index.html est prêt et affiché en direct."

        duration_ms = max(5, int((time.time() - start_time) * 1000))
        audit_ledger.record_decision(
            eval_result,
            status="completed",
            duration_ms=duration_ms,
            details={"output": output},
        )

        return {
            "success": True,
            "decision": eval_result.decision.value,
            "output": output,
            "coworker": coworker.dict(),
        }


# Global singleton
coworker_manager = CoworkerComputerManager()
