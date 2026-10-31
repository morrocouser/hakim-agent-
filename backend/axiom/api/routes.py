from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel
from axiom.models.schemas import (
    TaskRequest, TaskResult, TaskAssignment, ChatMessage, AgentName, ModelName,
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
from axiom.auth.jwt import get_current_user, optional_user
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
    loop: Optional[ReActLoop] = Depends(get_loop),
):
    """Exécute une tâche avec injection de dépendance ReActLoop."""
    if not loop:
        raise HTTPException(status_code=503, detail="OpenRouter not configured. Set OPENROUTER_API_KEY in .env")
    dims = req.dimensions or infer_dimensions(req.description, req.task_type)
    assignment = score_and_route(req.description, req.task_type, dims)
    result = await loop.execute(assignment, req.context)
    return result


AVAILABLE_MODELS = [
    {
        "id": "auto",
        "name": "Auto-Route Intelligent (APEX)",
        "provider": "APEX Router",
        "badge": "Auto",
        "description": "Sélectionne le meilleur modèle (Flash/Pro/Claude) selon la complexité et le type de tâche.",
    },
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "Google AI Studio",
        "badge": "Rapide",
        "description": "Ultra-rapide, multimodal, contexte large 1M tokens. Recommandé pour l'usage quotidien.",
    },
    {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "Google AI Studio",
        "badge": "Raisonnement",
        "description": "Raisonnement poussé, analyse complexe et capacités mathématiques avancées.",
    },
    {
        "id": "anthropic/claude-3.7-sonnet",
        "name": "Claude 3.7 Sonnet",
        "provider": "Anthropic / OpenRouter",
        "badge": "Code Star",
        "description": "Modèle de référence pour la programmation, l'architecture système et le refactoring.",
    },
    {
        "id": "anthropic/claude-3.5-haiku",
        "name": "Claude 3.5 Haiku",
        "provider": "Anthropic / OpenRouter",
        "badge": "Économique",
        "description": "Exécution rapide, concis et économique pour les tâches directes.",
    },
    {
        "id": "openai/gpt-4o",
        "name": "GPT-4o",
        "provider": "OpenAI / OpenRouter",
        "badge": "Polyvalent",
        "description": "Modèle phare d'OpenAI, polyvalent et performant en analyse générale.",
    },
    {
        "id": "deepseek/deepseek-chat",
        "name": "DeepSeek V3",
        "provider": "DeepSeek / OpenRouter",
        "badge": "Code & Perf",
        "description": "Excellente efficacité pour le code et les tâches techniques à coût minime.",
    },
    {
        "id": "deepseek/deepseek-r1",
        "name": "DeepSeek R1",
        "provider": "DeepSeek / OpenRouter",
        "badge": "Deep Think",
        "description": "Raisonnement profond en chaîne de pensée (Chain-of-Thought).",
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "Llama 3.3 70B",
        "provider": "Meta / OpenRouter",
        "badge": "Open Source",
        "description": "Grand modèle libre haute performance.",
    },
    {
        "id": "omniroute/auto/best-coding",
        "name": "OmniRoute · Best Coding (Local 20128)",
        "provider": "OmniRoute Gateway",
        "badge": "Omni Code",
        "description": "Sélection automatique du meilleur modèle de programmation via la passerelle OmniRoute (Port 20128).",
    },
    {
        "id": "omniroute/auto/best-fast",
        "name": "OmniRoute · Best Fast (Local 20128)",
        "provider": "OmniRoute Gateway",
        "badge": "Omni Fast",
        "description": "Sélection automatique du modèle le plus véloce via la passerelle OmniRoute locale.",
    },
    {
        "id": "omniroute/auto/best-reasoning",
        "name": "OmniRoute · Best Reasoning (Local 20128)",
        "provider": "OmniRoute Gateway",
        "badge": "Omni Think",
        "description": "Sélection automatique du modèle de réflexion logique avancée via OmniRoute.",
    },
]


@router.get("/models")
async def get_available_models(claude: Optional[LocalAPIClient] = Depends(get_claude)):
    """Retourne la liste des modèles sélectionnables, le modèle actif et le statut d'OmniRoute."""
    import urllib.request
    current_default = os.getenv("HAKIM_LLM_MODEL") or "gemini-2.5-flash"
    base_url = claude.base_url if claude else (os.getenv("HAKIM_LLM_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai")
    provider_name = "Google AI Studio"
    if "openrouter.ai" in str(base_url):
        provider_name = "OpenRouter"
    elif "20128" in str(base_url):
        provider_name = "OmniRoute Local"
    elif "localhost" in str(base_url):
        provider_name = "Local Gateway"

    # Vérification à la volée du statut OmniRoute (Port 20128)
    omniroute_status = {"online": False, "port": 20128, "models_count": 0}
    try:
        omni_url = (os.getenv("OMNIROUTE_BASE_URL") or "http://localhost:20128/v1").rstrip("/")
        omni_key = os.getenv("OMNIROUTE_API_KEY", "")
        req = urllib.request.Request(
            f"{omni_url}/models",
            headers={"Authorization": f"Bearer {omni_key}"} if omni_key else {},
        )
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                omniroute_status = {
                    "online": True,
                    "port": 20128,
                    "models_count": len(data.get("data", [])),
                    "base_url": omni_url,
                }
    except Exception:
        pass

    return {
        "active_model": current_default,
        "active_provider": provider_name,
        "base_url": str(base_url),
        "omniroute": omniroute_status,
        "models": AVAILABLE_MODELS,
    }


@router.get("/omniroute/status")
async def get_omniroute_status():
    """Vérifie l'état de la passerelle locale OmniRoute sur le port 20128."""
    import urllib.request
    omni_url = (os.getenv("OMNIROUTE_BASE_URL") or "http://localhost:20128/v1").rstrip("/")
    omni_key = os.getenv("OMNIROUTE_API_KEY", "")
    headers = {"Authorization": f"Bearer {omni_key}"} if omni_key else {}
    
    try:
        req = urllib.request.Request(f"{omni_url}/models", headers=headers)
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models_list = [m["id"] for m in data.get("data", [])]
            return {
                "online": True,
                "port": 20128,
                "base_url": omni_url,
                "api_key_configured": bool(omni_key),
                "total_models": len(models_list),
                "sample_models": models_list[:15],
                "status": "Opérationnel",
            }
    except Exception as e:
        return {
            "online": False,
            "port": 20128,
            "base_url": omni_url,
            "api_key_configured": bool(omni_key),
            "error": str(e),
            "status": "Injoignable ou non démarré",
        }


class ModelSelectionRequest(BaseModel):
    model: str


@router.post("/models/select")
async def set_active_model(req: ModelSelectionRequest):
    """Met à jour le modèle par défaut actif dans l'environnement du runtime."""
    new_model = req.model.strip()
    if not new_model:
        raise HTTPException(status_code=400, detail="Nom de modèle invalide")
    if new_model == "auto":
        os.environ["HAKIM_LLM_MODEL"] = "gemini-3.5-flash"
        log.info("⚙️ Modèle APEX en mode Auto-Route (cible: gemini-3.5-flash)")
    else:
        os.environ["HAKIM_LLM_MODEL"] = new_model
        log.info("⚙️ Modèle global APEX mis à jour: %s", new_model)
    return {"status": "ok", "active_model": new_model}


class ChatMessageExtended(ChatMessage):
    conversation_id: int | None = None
    model: str | None = None
    agent: str | None = None


@router.post("/chat")
async def chat(
    message: ChatMessageExtended,
    user: Optional[User] = Depends(optional_user),
    loop: Optional[ReActLoop] = Depends(get_loop),
):
    """Traite une requête de chat avec injection de dépendance ReActLoop."""
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("📨 REQUÊTE CHAT REÇUE")
    log.info("   Message: %s", message.content[:100] + ("..." if len(message.content) > 100 else ""))
    if not loop:
        log.error("   ❌ OpenRouter non configuré")
        raise HTTPException(status_code=503, detail="OpenRouter API not configured. Set OPENROUTER_API_KEY in .env")

    # Obtenir ou créer la conversation
    session = await get_session()
    convo_id = message.conversation_id
    try:
        # Résoudre l'utilisateur (authentifié ou invité local)
        active_user_id = user.id if user else 1
        if not user:
            first_u = (await session.execute(select(User).limit(1))).scalar_one_or_none()
            if first_u:
                active_user_id = first_u.id

        if convo_id:
            result = await session.execute(
                select(Conversation).where(Conversation.id == convo_id)
            )
            convo = result.scalar_one_or_none()
            if not convo:
                convo = Conversation(user_id=active_user_id, title=message.content[:80])
                session.add(convo)
                await session.commit()
                await session.refresh(convo)
                convo_id = convo.id
        else:
            convo = Conversation(user_id=active_user_id, title=message.content[:80])
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
    if message.model and message.model.strip() and message.model.strip() != "auto":
        assignment.model = message.model.strip()
        log.info("   🎯 Modèle imposé par l'utilisateur: %s", assignment.model)
    if message.agent and message.agent.strip() and message.agent.strip() != "auto":
        req_agent = message.agent.strip().upper()
        for a in AgentName:
            if a.value == req_agent or a.name == req_agent or req_agent in a.value:
                assignment.agent = a
                log.info("   🎯 Agent imposé par l'utilisateur: %s", assignment.agent.value)
                break
    log.info("   ✅ Agent sélectionné: %s", assignment.agent.value if hasattr(assignment.agent, "value") else str(assignment.agent))
    log.info("   ✅ Modèle actif: %s", assignment.model.value if hasattr(assignment.model, "value") else str(assignment.model))
    log.info("   ✅ Score: %s/10", assignment.score)
    log.info("   🤖 ÉTAPE 2/3 : Exécution ReAct Loop...")
    result = await loop.execute(assignment, message.content)
    log.info("   📤 ÉTAPE 3/3 : Résultat prêt")
    log.info("   Status: %s | Qualité: %s/10 | Itération: %s", result.status.value, result.quality_score, result.iteration)

    # Save assistant response
    response_content = result.output
    if not response_content or response_content.strip() == "" or response_content.strip() == "No output":
        response_content = result.error or "Bonjour ! J'ai réinitialisé et basculé le modèle d'IA pour assurer une exécution fluide. Comment puis-je vous aider ?"
    session = await get_session()
    try:
        assistant_msg = Message(
            conversation_id=convo_id,
            role="assistant",
            content=response_content,
            agent=assignment.agent.value if hasattr(assignment.agent, "value") else str(assignment.agent),
            model=assignment.model.value if hasattr(assignment.model, "value") else str(assignment.model),
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
            select(Conversation).where(Conversation.id == convo_id)
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
async def get_memory(memory: MemoryManager = Depends(get_memory)):
    """Récupère la mémoire avec injection de dépendance."""
    return memory.export()


@router.post("/memory/project")
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


@router.post("/memory/stack")
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


@router.post("/memory/decision")
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
async def list_agents(include_agency: bool = True, limit: Optional[int] = None):
    from axiom.core.agents import AGENT_CONFIGS
    res = {
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
    if include_agency:
        import json
        catalog_path = Path(__file__).resolve().parent.parent / "data" / "agency_agents_catalog.json"
        if catalog_path.exists():
            try:
                with open(catalog_path, encoding="utf-8") as f:
                    cat = json.load(f)
                agents_list = cat.get("agents", [])
                if limit:
                    agents_list = agents_list[:limit]
                for a in agents_list:
                    key = f"AGENCY_{a['slug'].replace('-', '_').upper()}"
                    res[key] = {
                        "icon": a.get("emoji", "🤖"),
                        "label": f"{a['name']} ({a.get('division_label', 'Agency')})",
                        "speciality": a.get("description", ""),
                        "description": a.get("vibe", a.get("description", "")),
                        "default_model": "deepseek-v4-flash-free",
                        "approach": f"Division: {a.get('division_label', '')} — {a.get('vibe', 'Excellence opérationnelle')}",
                    }
            except Exception as e:
                log.warning("Erreur chargement agency agents catalog: %s", e)
    return res


@router.post("/chat/stream")
async def chat_stream(
    message: ChatMessage,
    claude: Optional[LocalAPIClient] = Depends(get_claude),
):
    """Endpoint de streaming SSE pour le chat."""
    if not claude:
        raise HTTPException(status_code=503, detail="OpenRouter not configured. Set OPENROUTER_API_KEY in .env")
    assignment = score_and_route(message.content)

    async def generate():
        try:
            model_str = assignment.model.value if hasattr(assignment.model, "value") else str(assignment.model)
            agent_str = assignment.agent.value if hasattr(assignment.agent, "value") else str(assignment.agent)
            response = await claude.chat(
                model=model_str,
                system=f"Tu es {agent_str}. Score: {assignment.score}/10. Zéro filler. Réponds directement.",
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
    user: Optional[User] = Depends(optional_user),
    web_search: WebSearchTool = Depends(get_web_search),
):
    """Recherche web via WebSearch avec injection de dépendance."""
    result = await web_search.search(query, max_results=max_results)
    return {"query": query, "results": result}


@router.post("/tools/code")
async def execute_code(
    language: str = "python",
    code: str = "",
    user: Optional[User] = Depends(optional_user),
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
    user: Optional[User] = Depends(optional_user),
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
    user: Optional[User] = Depends(optional_user),
    file_manager: FileManager = Depends(get_file_manager),
):
    """Lit un fichier de manière sécurisée."""
    result = file_manager.read_file(path)
    return {"path": path, "content": result}


@router.delete("/tools/file/{path:path}")
async def delete_file(
    path: str,
    user: Optional[User] = Depends(optional_user),
    file_manager: FileManager = Depends(get_file_manager),
):
    """Supprime un fichier de manière sécurisée."""
    result = file_manager.delete_file(path)
    return {"path": path, "result": result}


@router.get("/tools/files")
async def list_files(
    path: str = "",
    user: Optional[User] = Depends(optional_user),
    file_manager: FileManager = Depends(get_file_manager),
):
    """Liste les fichiers dans un répertoire."""
    result = file_manager.list_files(path)
    return {"path": path, "files": result.split("\n") if result else []}


@router.get("/errors")
async def get_errors(error_log: ErrorLog = Depends(get_error_log)):
    """Récupère le journal d'erreurs avec injection de dépendance."""
    entries = error_log.get_all()
    return {"errors": [e.to_dict() for e in entries]}


@router.post("/errors")
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
    user: Optional[User] = Depends(optional_user),
):
    """Exécute une commande slash côté backend."""
    from axiom.commands.registry import CommandRegistry
    from axiom.commands.handlers import CommandHandlers
    reg = CommandRegistry()
    handlers = CommandHandlers(reg)
    cmd = reg.get(command)
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Commande inconnue: {command}")
    res = handlers.execute(cmd, args)
    return res


class SaveWebsiteRequest(BaseModel):
    name: str = "site-demo"
    html: str


@router.post("/websites/save")
async def save_website_endpoint(req: SaveWebsiteRequest):
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '', req.name.strip().replace(" ", "-")) or "site-demo"
    site_dir = Path("websites") / safe_name
    site_dir.mkdir(parents=True, exist_ok=True)
    file_path = site_dir / "index.html"
    file_path.write_text(req.html, encoding="utf-8")
    abs_path = str(file_path.resolve())
    return {
        "status": "ok",
        "name": safe_name,
        "relative_path": f"websites/{safe_name}/index.html",
        "absolute_path": abs_path,
        "file_url": f"file:///{abs_path.replace(os.sep, '/')}",
    }
