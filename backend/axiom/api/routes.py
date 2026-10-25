from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from axiom.models.schemas import (
    TaskRequest, TaskResult, TaskAssignment, ChatMessage,
)
from axiom.core.scoring import score_and_route, infer_dimensions
from axiom.core.react_loop import ReActLoop
from axiom.claude.client import LocalAPIClient
from axiom.core.memory import MemoryManager
from axiom.tools.web_search import WebSearchTool
from axiom.tools.code_executor import CodeExecutor
from axiom.tools.file_manager import FileManager
from axiom.tools.error_log import ErrorLog
from axiom.logging_setup import log
from axiom.db.models import Conversation, Message, User, get_session
from axiom.auth.jwt import get_current_user, require_admin, is_admin
from sqlalchemy import select
import json
import asyncio
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Charger .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

router = APIRouter(prefix="/api/v1")


# =============================================================================
# DÉPENDANCES POUR L'INJECTION DE DÉPENDANCES
# =============================================================================

class ServiceDependencies:
    """
    Conteneur pour les dépendances de service.
    Utilise le pattern Singleton pour s'assurer qu'une seule instance
    est créée par processus.
    """
    _instance: Optional["ServiceDependencies"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Initialiser toutes les dépendances
        self.memory = MemoryManager()
        
        try:
            self.claude = LocalAPIClient()
            self.loop = ReActLoop(self.memory, self.claude)
        except ValueError as e:
            self.claude = None
            self.loop = None
            log.warning("LLM provider non configuré: %s", e)
        
        self.web_search = WebSearchTool(os.getenv("WEB_SEARCH_API_KEY", ""))
        self.code_executor = CodeExecutor()
        self.file_manager = FileManager()
        self.error_log = ErrorLog(os.getenv("ERROR_LOG_PATH", ""))
        
        self._initialized = True
        log.info("ServiceDependencies initialisé")


# Créer l'instance singleton
_dependencies = ServiceDependencies()


def get_dependencies() -> ServiceDependencies:
    """Retourne les dépendances de service (singleton)."""
    return _dependencies


def get_memory() -> MemoryManager:
    """Retourne le MemoryManager."""
    return get_dependencies().memory


def get_claude() -> Optional[LocalAPIClient]:
    """Retourne le client Claude/LLM."""
    return get_dependencies().claude


def get_loop() -> Optional[ReActLoop]:
    """Retourne la boucle ReAct."""
    return get_dependencies().loop


def get_web_search() -> WebSearchTool:
    """Retourne l'outil de recherche web."""
    return get_dependencies().web_search


def get_code_executor() -> CodeExecutor:
    """Retourne l'exécuteur de code."""
    return get_dependencies().code_executor


def get_file_manager() -> FileManager:
    """Retourne le gestionnaire de fichiers."""
    return get_dependencies().file_manager


def get_error_log() -> ErrorLog:
    """Retourne le journal d'erreurs."""
    return get_dependencies().error_log


def require_claude(loop: Optional[ReActLoop] = Depends(get_loop)):
    """Vérifie que le client LLM est configuré."""
    if not loop:
        raise HTTPException(
            status_code=503,
            detail="LLM API not configured. Set HAKIM_LLM_API_KEY in .env (OpenCode Zen or OpenRouter)"
        )
    return loop


@router.get("/health")
async def health(
    claude: Optional[LocalAPIClient] = Depends(get_claude),
    memory: MemoryManager = Depends(get_memory),
):
    """Endpoint de santé avec injection de dépendances."""
    return {
        "status": "ok",
        "agent": "APEX",
        "version": "4.0.0",
        "openrouter_configured": claude.is_configured() if claude else False,
        "provider": "OpenCode Zen" if claude and "opencode.ai" in (claude.base_url or "") else "OpenRouter" if claude else "none",
        "memory_tokens": memory.get_total_tokens_estimate(),
    }


@router.post("/score", response_model=TaskAssignment)
async def score_task(req: TaskRequest):
    dims = req.dimensions or infer_dimensions(req.description, req.task_type)
    return score_and_route(req.description, req.task_type, dims)


@router.post("/execute", response_model=TaskResult)
async def execute_task(
    req: TaskRequest,
    user: User = Depends(get_current_user),
    loop: Optional[ReActLoop] = Depends(get_loop),
):
    """Exécute une tâche avec injection de dépendance ReActLoop."""
    if not loop:
        raise HTTPException(status_code=503, detail="OpenRouter not configured. Set OPENROUTER_API_KEY in .env")
    dims = req.dimensions or infer_dimensions(req.description, req.task_type)
    assignment = score_and_route(req.description, req.task_type, dims)
    result = await loop.execute(assignment, req.context)
    return result


class ChatMessageExtended(ChatMessage):
    conversation_id: int | None = None


@router.post("/chat")
async def chat(
    message: ChatMessageExtended,
    user: User = Depends(get_current_user),
    loop: Optional[ReActLoop] = Depends(get_loop),
):
    """Traite une requête de chat avec injection de dépendance ReActLoop."""
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("📨 REQUÊTE CHAT REÇUE")
    log.info("   Message: %s", message.content[:100] + ("..." if len(message.content) > 100 else ""))
    if not loop:
        log.error("   ❌ OpenRouter non configuré")
        raise HTTPException(status_code=503, detail="OpenRouter API not configured. Set OPENROUTER_API_KEY in .env")

    # Get or create conversation
    session = await get_session()
    convo_id = message.conversation_id
    try:
        if convo_id:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == convo_id, Conversation.user_id == user.id
                )
            )
            convo = result.scalar_one_or_none()
            if not convo:
                raise HTTPException(status_code=404, detail="Conversation non trouvée")
        else:
            convo = Conversation(user_id=user.id, title=message.content[:80])
            session.add(convo)
            await session.commit()
            await session.refresh(convo)
            convo_id = convo.id

        # Save user message
        user_msg = Message(
            conversation_id=convo_id,
            role="user",
            content=message.content,
        )
        session.add(user_msg)
        await session.commit()
    finally:
        await session.close()

    log.info("   🔍 ÉTAPE 1/3 : Scoring & Routing...")
    assignment = score_and_route(message.content)
    log.info("   ✅ Agent sélectionné: %s", assignment.agent.value)
    log.info("   ✅ Modèle: %s", assignment.model.value)
    log.info("   ✅ Score: %s/10", assignment.score)
    log.info("   🤖 ÉTAPE 2/3 : Exécution ReAct Loop...")
    result = await loop.execute(assignment, message.content)
    log.info("   📤 ÉTAPE 3/3 : Résultat prêt")
    log.info("   Status: %s | Qualité: %s/10 | Itération: %s", result.status.value, result.quality_score, result.iteration)

    # Save assistant response
    response_content = result.output or result.error or "No output"
    session = await get_session()
    try:
        assistant_msg = Message(
            conversation_id=convo_id,
            role="assistant",
            content=response_content,
            agent=assignment.agent.value,
            model=assignment.model.value,
            score=assignment.score,
            extra_data={
                "status": result.status.value,
                "quality_score": result.quality_score,
                "iteration": result.iteration,
            },
        )
        session.add(assistant_msg)

        # Update conversation timestamp
        convo_result = await session.execute(
            select(Conversation).where(
                Conversation.id == convo_id, Conversation.user_id == user.id
            )
        )
        convo = convo_result.scalar_one_or_none()
        if convo:
            convo.updated_at = datetime.utcnow()

        await session.commit()
    finally:
        await session.close()

    log.info("   💾 Message sauvegardé (convo=%s)", convo_id)
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    return {
        "response": response_content,
        "task": result.model_dump(),
        "conversation_id": convo_id,
    }


@router.get("/memory")
async def read_memory(
    user: User = Depends(get_current_user),
    memory: MemoryManager = Depends(get_memory),
):
    """Récupère la mémoire avec injection de dépendance."""
    return memory.export()


@router.post("/memory/project", dependencies=[Depends(require_admin)])
async def set_project(
    name: str,
    project_type: str = "SaaS",
    description: str = "",
    client: str = "Interne",
    memory: MemoryManager = Depends(get_memory),
):
    """Configure un projet en mémoire."""
    memory.set_project(name, project_type, description, client=client)
    return {"status": "ok"}


@router.post("/memory/stack", dependencies=[Depends(require_admin)])
async def set_stack(
    frontend: str = "",
    backend: str = "",
    database: str = "",
    auth: str = "",
    infra: str = "",
    testing: str = "",
    ci_cd: str = "",
    memory: MemoryManager = Depends(get_memory),
):
    """Configure une stack technique en mémoire."""
    memory.set_stack(frontend, backend, database, auth, infra, testing, ci_cd)
    return {"status": "ok"}


@router.post("/memory/decision", dependencies=[Depends(require_admin)])
async def add_decision(
    decision: str,
    reason: str,
    revocable: bool = False,
    memory: MemoryManager = Depends(get_memory),
):
    """Ajoute une décision architecturale en mémoire."""
    memory.add_decision(decision, reason, revocable)
    return {"status": "ok"}


@router.get("/agents")
async def list_agents():
    from axiom.core.agents import AGENT_CONFIGS
    return {
        name.value: {
            "icon": cfg.icon,
            "label": cfg.label,
            "speciality": cfg.speciality,
            "description": cfg.description,
            "default_model": cfg.default_model.value,
            "approach": cfg.approach,
        }
        for name, cfg in AGENT_CONFIGS.items()
    }


@router.post("/chat/stream")
async def chat_stream(
    message: ChatMessage,
    user: User = Depends(get_current_user),
    claude: Optional[LocalAPIClient] = Depends(get_claude),
):
    """Endpoint de streaming SSE pour le chat."""
    if not claude:
        raise HTTPException(status_code=503, detail="OpenRouter not configured. Set OPENROUTER_API_KEY in .env")
    assignment = score_and_route(message.content)

    async def generate():
        try:
            response = await claude.chat(
                model=assignment.model.value,
                system=f"Tu es {assignment.agent.value}. Score: {assignment.score}/10. Zéro filler. Réponds directement.",
                messages=[{"role": "user", "content": message.content}],
                max_tokens=4096,
            )
            # Stream en chunks pour simuler le streaming
            chunk_size = 20
            for i in range(0, len(response), chunk_size):
                yield f"data: {json.dumps({'chunk': response[i:i+chunk_size]})}\n\n"
                await asyncio.sleep(0.01)
            yield f"data: {json.dumps({'done': True, 'task': assignment.model_dump()})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/tools/search")
async def web_search_endpoint(
    query: str,
    max_results: int = 5,
    user: User = Depends(get_current_user),
    web_search: WebSearchTool = Depends(get_web_search),
):
    """Recherche web via WebSearch avec injection de dépendance."""
    result = await web_search.search(query, max_results=max_results)
    return {"query": query, "results": result}


@router.post("/tools/code")
async def execute_code(
    language: str = "python",
    code: str = "",
    user: User = Depends(get_current_user),
    code_executor: CodeExecutor = Depends(get_code_executor),
):
    """
    Exécute du code de façon contrôlée et sécurisée.
    
    Sécurité:
    - Validation du langage (python/javascript uniquement)
    - Validation du code (pas d'imports dangereux)
    - Exécution dans Docker sandbox
    - Limites de ressources appliquées
    """
    # Validation d'input
    if not code or not code.strip():
        raise HTTPException(status_code=400, detail="Code requis")
    
    language = language.lower()
    if language not in ("python", "javascript"):
        raise HTTPException(
            status_code=400,
            detail=f"Langage non supporté: {language}. Utilisez 'python' ou 'javascript'"
        )
    
    # Limiter la taille du code
    if len(code) > 50_000:
        raise HTTPException(status_code=400, detail="Code trop long (max 50KB)")
    
    result = code_executor.execute(language, code)
    return {"language": language, "output": result}


@router.post("/tools/file")
async def create_file(
    path: str,
    content: str = "",
    user: User = Depends(get_current_user),
    file_manager: FileManager = Depends(get_file_manager),
):
    """
    Crée un fichier dans le workspace de manière sécurisée.
    
    Sécurité:
    - Validation du chemin (pas de path traversal)
    - Validation de l'extension
    - Validation du contenu (taille, UTF-8)
    - Répertoire isolé
    """
    # Validation d'input
    if not path or not path.strip():
        raise HTTPException(status_code=400, detail="Chemin requis")
    
    # Limiter la taille du chemin
    if len(path) > 255:
        raise HTTPException(status_code=400, detail="Chemin trop long (max 255 caractères)")
    
    # Limiter la taille du contenu
    if len(content.encode("utf-8")) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="Contenu trop grand (max 10MB)")
    
    # Bloquer les chemins absolus
    if path.startswith("/") or path.startswith("\\"):
        raise HTTPException(
            status_code=400,
            detail="Chemin absolu non autorisé. Utilisez un chemin relatif."
        )
    
    result = file_manager.create_file(path, content)
    return {"result": result}


@router.get("/tools/file/{path:path}")
async def read_file(
    path: str,
    user: User = Depends(get_current_user),
    file_manager: FileManager = Depends(get_file_manager),
):
    """Lit un fichier de manière sécurisée."""
    result = file_manager.read_file(path)
    return {"path": path, "content": result}


@router.delete("/tools/file/{path:path}")
async def delete_file(
    path: str,
    user: User = Depends(get_current_user),
    file_manager: FileManager = Depends(get_file_manager),
):
    """Supprime un fichier de manière sécurisée."""
    result = file_manager.delete_file(path)
    return {"path": path, "result": result}


@router.get("/tools/files")
async def list_files(
    path: str = "",
    user: User = Depends(get_current_user),
    file_manager: FileManager = Depends(get_file_manager),
):
    """Liste les fichiers dans un répertoire."""
    result = file_manager.list_files(path)
    return {"path": path, "files": result.split("\n") if result else []}


@router.get("/errors")
async def get_errors(
    user: User = Depends(get_current_user),
    error_log: ErrorLog = Depends(get_error_log),
):
    """Récupère le journal d'erreurs avec injection de dépendance."""
    entries = error_log.get_all()
    return {"errors": [e.to_dict() for e in entries]}


@router.post("/errors", dependencies=[Depends(require_admin)])
async def log_error_endpoint(
    tier: int = 1,
    agent: str = "",
    context: str = "",
    symptom: str = "",
    root_cause: str = "",
    fix: str = "",
    lesson: str = "",
    score: int = 5,
    error_log: ErrorLog = Depends(get_error_log),
):
    """Log une erreur apprise avec injection de dépendance."""
    if not symptom or not root_cause or not fix:
        raise HTTPException(status_code=400, detail="symptom, root_cause et fix requis")
    entry = error_log.log(
        tier=tier, agent=agent, context=context, symptom=symptom,
        root_cause=root_cause, fix=fix, lesson=lesson, score=score,
    )
    return {"id": entry.id, "status": "logged"}


@router.get("/skills")
async def list_skills(limit: int = 500, query: str = ""):
    """Liste les skills intégrés (provenant des dépôts GitHub de skills)."""
    from axiom.skills_catalog import list_skills, search_skills
    if query:
        skills = search_skills(query, limit=limit)
    else:
        skills = list_skills()[:limit]
    return {"total": len(skills), "skills": skills}


@router.get("/skills/{repo}/{skill}")
async def get_skill(repo: str, skill: str, readme: bool = False):
    """Détail d'un skill : metadata, et éventuellement son SKILL.md."""
    from axiom.skills_catalog import get_skill, get_skill_readme
    meta = get_skill(repo, skill)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Skill introuvable: {repo}/{skill}")
    result = dict(meta)
    if readme:
        result["content"] = get_skill_readme(repo, skill)
    return result


@router.get("/skills/find")
async def find_skills_endpoint(query: str = "", limit: int = 20):
    """Recherche dynamique de compétences (skills) dans le catalogue."""
    from axiom.agent_skills_catalog import find_skills
    skills = find_skills(query=query, limit=limit)
    return {"total": len(skills), "query": query, "skills": skills}


@router.get("/commands")
async def list_commands():
    """Liste l'ensemble des commandes slash disponibles."""
    from axiom.commands.registry import CommandRegistry
    reg = CommandRegistry()
    cmds = []
    for cmd in reg.list_all():
        cmds.append({
            "name": cmd.name,
            "description": cmd.description,
            "group": cmd.group.value,
            "usage": cmd.usage,
            "examples": cmd.examples,
        })
    return {"total": len(cmds), "commands": cmds}


@router.post("/commands/execute")
async def execute_command(
    command: str,
    args: str = "",
    user: User = Depends(get_current_user),
):
    """Exécute une commande slash côté backend.

    Les commandes qui lancent des processus (shell, git, docker, cloud, ...)
    sont réservées aux administrateurs (HAKIM_ADMIN_USERS).
    """
    from axiom.commands.registry import CommandRegistry
    from axiom.commands.handlers import CommandHandlers
    reg = CommandRegistry()
    handlers = CommandHandlers(reg)
    cmd = reg.get(command)
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Commande inconnue: {command}")
    if handlers.spawns_process(cmd) and not is_admin(user):
        raise HTTPException(status_code=403, detail="Droits administrateur requis pour cette commande")
    res = handlers.execute(cmd, args)
    return res
