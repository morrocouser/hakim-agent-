from axiom.models.schemas import (
    ScoringDimensions, ScoringWeights, ModelName, AgentName,
    TaskType, TaskAssignment,
)
from axiom.logging_setup import log
from typing import Optional, Any, Union
import uuid

DEFAULT_WEIGHTS = ScoringWeights()

MODEL_THRESHOLDS = [
    (0.0, 2.5, ModelName.SMALL),
    (2.6, 4.5, ModelName.MEDIUM),
    (4.6, 6.5, ModelName.LARGE),
    (6.6, 10.0, ModelName.BEST),
]

# Override: modele rapide pour taches urgentes (modele small = Gemini Flash)
URGENT_OVERRIDE = ModelName.SMALL

# Échelle de repli dynamique (Fallback Ladder) par modèle
MODEL_FALLBACK_LADDER: dict[str, list[str]] = {
    ModelName.BEST.value: [
        ModelName.LARGE.value,
        ModelName.FLASH.value,
        "gemini-3.5-flash",
        "omniroute/auto/best-fast",
        ModelName.MEDIUM.value,
        ModelName.SMALL.value,
    ],
    ModelName.LARGE.value: [
        ModelName.FLASH.value,
        "gemini-3.5-flash",
        "omniroute/auto/best-fast",
        ModelName.MEDIUM.value,
        ModelName.SMALL.value,
    ],
    ModelName.MEDIUM.value: [
        ModelName.SMALL.value,
        ModelName.FLASH.value,
        "gemini-3.5-flash",
        "omniroute/auto/best-fast",
    ],
    ModelName.SMALL.value: [
        "gemini-3.5-flash",
        ModelName.FLASH.value,
        "omniroute/auto/best-fast",
        ModelName.BEST.value,
    ],
    ModelName.FLASH.value: [
        "gemini-3.5-flash",
        ModelName.SMALL.value,
        "omniroute/auto/best-fast",
        ModelName.BEST.value,
    ],
    ModelName.CODE.value: [
        "gemini-3.5-flash",
        "omniroute/auto/best-coding",
        ModelName.BEST.value,
    ],
    ModelName.LAGUNA.value: [
        "gemini-3.5-flash",
        ModelName.BEST.value,
    ],
    ModelName.FALLBACK.value: [
        "gemini-3.5-flash",
        "omniroute/auto/best-fast",
        ModelName.SMALL.value,
    ],
}

AGENT_ROUTING: dict[str, list[AgentName]] = {
    "architecture": [AgentName.ARCHITECT],
    "system design": [AgentName.ARCHITECT],
    "scalable": [AgentName.ARCHITECT],
    "microservices": [AgentName.ARCHITECT],
    "code": [AgentName.CODER],
    "coder": [AgentName.CODER],
    "coding": [AgentName.CODER],
    "implémenter": [AgentName.CODER],
    "implémentation": [AgentName.CODER],
    "fonction": [AgentName.CODER],
    "composant": [AgentName.CODER],
    "refactor": [AgentName.CODER],
    "refactoring": [AgentName.CODER],
    "test": [AgentName.CODER, AgentName.DEBUGGER],
    "tests": [AgentName.CODER, AgentName.DEBUGGER],
    "bug": [AgentName.DEBUGGER],
    "bugs": [AgentName.DEBUGGER],
    "erreur": [AgentName.DEBUGGER],
    "erreurs": [AgentName.DEBUGGER],
    "crash": [AgentName.DEBUGGER],
    "crashes": [AgentName.DEBUGGER],
    "stack trace": [AgentName.DEBUGGER],
    "data": [AgentName.ANALYST],
    "sql": [AgentName.ANALYST],
    "statistique": [AgentName.ANALYST],
    "statistiques": [AgentName.ANALYST],
    "dashboard": [AgentName.ANALYST],
    "csv": [AgentName.ANALYST],
    "json": [AgentName.ANALYST],
    "document": [AgentName.WRITER],
    "documentation": [AgentName.WRITER],
    "readme": [AgentName.WRITER],
    "rapport": [AgentName.WRITER],
    "email": [AgentName.WRITER],
    "contenu": [AgentName.WRITER],
    "recherche": [AgentName.RESEARCHER],
    "rechercher": [AgentName.RESEARCHER],
    "actualité": [AgentName.RESEARCHER],
    "actualités": [AgentName.RESEARCHER],
    "comparer": [AgentName.RESEARCHER],
    "comparaison": [AgentName.RESEARCHER],
    "plan": [AgentName.PLANNER],
    "planifier": [AgentName.PLANNER],
    "roadmap": [AgentName.PLANNER],
    "stratégie": [AgentName.PLANNER],
    "sprint": [AgentName.PLANNER],
    "cahier des charges": [AgentName.PLANNER],
    "site": [AgentName.WEB_BUILDER],
    "site web": [AgentName.WEB_BUILDER],
    "siteweb": [AgentName.WEB_BUILDER],
    "page web": [AgentName.WEB_BUILDER],
    "landing page": [AgentName.WEB_BUILDER],
    "créer un site": [AgentName.WEB_BUILDER],
    "creer un site": [AgentName.WEB_BUILDER],
    "crée un site": [AgentName.WEB_BUILDER],
    "cree un site": [AgentName.WEB_BUILDER],
    "créer site": [AgentName.WEB_BUILDER],
    "creer site": [AgentName.WEB_BUILDER],
    "website": [AgentName.WEB_BUILDER],
    "web design": [AgentName.WEB_BUILDER],
    "webdesign": [AgentName.WEB_BUILDER],
    "portfolio": [AgentName.WEB_BUILDER],
    "vitrine": [AgentName.WEB_BUILDER],
    "maquette web": [AgentName.WEB_BUILDER],
    "frontend": [AgentName.WEB_BUILDER, AgentName.CODER],
    "html": [AgentName.WEB_BUILDER],
    "css": [AgentName.WEB_BUILDER],
    "tailwind": [AgentName.WEB_BUILDER],
    "site internet": [AgentName.WEB_BUILDER],
    "creation de site": [AgentName.WEB_BUILDER],
    "création de site": [AgentName.WEB_BUILDER],
    "creation site": [AgentName.WEB_BUILDER],
    "création site": [AgentName.WEB_BUILDER],
    "faire un site": [AgentName.WEB_BUILDER],
    "fait un site": [AgentName.WEB_BUILDER],
    "web builder": [AgentName.WEB_BUILDER],
    "builder de site": [AgentName.WEB_BUILDER],
    "créateur de site": [AgentName.WEB_BUILDER],
    "createur de site": [AgentName.WEB_BUILDER],
    "autods": [AgentName.WEB_BUILDER],
    "dropshipping site": [AgentName.WEB_BUILDER],
    "boutique en ligne": [AgentName.WEB_BUILDER],
    "e-commerce": [AgentName.WEB_BUILDER],
    "ecommerce": [AgentName.WEB_BUILDER],
    "saas landing": [AgentName.WEB_BUILDER],
    "page d'accueil": [AgentName.WEB_BUILDER],
    "homepage": [AgentName.WEB_BUILDER],
    "web app": [AgentName.WEB_BUILDER],
    "webapp": [AgentName.WEB_BUILDER],
    "ui web": [AgentName.WEB_BUILDER],
}

AGENT_FALLBACK: dict[AgentName, AgentName] = {
    AgentName.ARCHITECT: AgentName.CODER,
    AgentName.CODER: AgentName.WRITER,
    AgentName.DEBUGGER: AgentName.CODER,
    AgentName.ANALYST: AgentName.CODER,
    AgentName.WRITER: AgentName.WRITER,
    AgentName.RESEARCHER: AgentName.WRITER,
    AgentName.PLANNER: AgentName.ARCHITECT,
    AgentName.QUICKSHOT: AgentName.WRITER,
    AgentName.WEB_BUILDER: AgentName.CODER,
}


def calculate_score(dimensions: ScoringDimensions, weights: Optional[ScoringWeights] = None) -> float:
    w = weights or DEFAULT_WEIGHTS
    return (
        (w.complexity * dimensions.complexity)
        + (w.stakes * dimensions.stakes)
        + (w.creativity * dimensions.creativity)
        + (w.speed * dimensions.speed_need)
        + (w.domain * dimensions.domain_match)
    )


def get_fallback_model(
    current_model: str | ModelName,
    registry: Optional[Any] = None,
) -> tuple[str, bool]:
    """
    Sélectionne le prochain modèle viable dans l'échelle de repli dont le disjoncteur est disponible.
    
    Returns:
        tuple (nouveau_modèle_str, est_un_repli_bool)
    """
    from axiom.core.circuit_breaker import circuit_breakers
    cb_registry = registry or circuit_breakers

    current_val = current_model.value if isinstance(current_model, ModelName) else str(current_model)
    ladder = MODEL_FALLBACK_LADDER.get(current_val, [ModelName.FALLBACK.value, "local:default"])

    for candidate in ladder:
        service_key = f"llm:{candidate}"
        if cb_registry.is_available(service_key):
            log.info("🔄 REPLI MODÈLE DISPONIBLE: %s -> %s", current_val, candidate)
            return candidate, True

    log.warning("⚠️ Tous les disjoncteurs modèles sont ouverts. Repli vers gemini-3.5-flash.")
    return "gemini-3.5-flash", True


def select_model(score: float, dimensions: ScoringDimensions, check_breaker: bool = True) -> ModelName:
    base_model = ModelName.BEST
    if dimensions.stakes >= 9:
        base_model = ModelName.BEST
    elif dimensions.speed_need <= 3 and score > 6:
        base_model = URGENT_OVERRIDE
    else:
        for low, high, model in MODEL_THRESHOLDS:
            if low <= score <= high:
                base_model = model
                break

    if check_breaker:
        from axiom.core.circuit_breaker import circuit_breakers
        if not circuit_breakers.is_available(f"llm:{base_model.value}"):
            fallback_val, _ = get_fallback_model(base_model, circuit_breakers)
            for m in ModelName:
                if m.value == fallback_val:
                    log.info("🔌 Circuit ouvert pour %s -> routage direct vers %s", base_model.value, m.value)
                    return m
            return ModelName.FALLBACK
    return base_model


def select_agent(description: str, task_type: TaskType) -> AgentName:
    desc_lower = description.lower()
    
    # Check for keyword matches (full words or subphrases)
    import re
    for keyword, agents in AGENT_ROUTING.items():
        pattern = rf'\b{re.escape(keyword)}\b' if ' ' not in keyword else re.escape(keyword)
        if re.search(pattern, desc_lower):
            return agents[0]
    
    # Fallback to task_type-based routing
    type_map: dict[TaskType, AgentName] = {
        TaskType.CODE: AgentName.CODER,
        TaskType.DEBUG: AgentName.DEBUGGER,
        TaskType.ARCH: AgentName.ARCHITECT,
        TaskType.DATA: AgentName.ANALYST,
        TaskType.DOC: AgentName.WRITER,
        TaskType.RESEARCH: AgentName.RESEARCHER,
        TaskType.PLAN: AgentName.PLANNER,
        TaskType.QUICK: AgentName.QUICKSHOT,
        TaskType.WEB: AgentName.WEB_BUILDER,
    }
    return type_map.get(task_type, AgentName.QUICKSHOT)




def infer_dimensions(description: str, task_type: TaskType) -> ScoringDimensions:
    d = ScoringDimensions()
    desc_lower = description.lower()
    task_type_map: dict[TaskType, tuple[float, float, float, float, float]] = {
        TaskType.CODE:     (6.0, 6.0, 5.0, 6.0, 6.0),
        TaskType.DEBUG:    (8.0, 8.0, 5.0, 7.0, 7.0),
        TaskType.ARCH:     (8.0, 7.0, 7.0, 5.0, 7.0),
        TaskType.DATA:     (6.0, 5.0, 4.0, 5.0, 6.0),
        TaskType.DOC:      (3.0, 3.0, 5.0, 4.0, 3.0),
        TaskType.RESEARCH: (5.0, 4.0, 3.0, 5.0, 5.0),
        TaskType.PLAN:     (7.0, 6.0, 6.0, 5.0, 6.0),
        TaskType.QUICK:    (2.0, 2.0, 2.0, 2.0, 3.0),
        TaskType.WEB:      (6.0, 5.0, 8.0, 6.0, 7.0),
    }
    if task_type in task_type_map:
        vals = task_type_map[task_type]
        d.complexity, d.stakes, d.creativity, d.speed_need, d.domain_match = vals
    complex_keywords = ["complex", "avancé", "architecture", "multi-étape", "distribué", "concurrence"]
    if any(k in desc_lower for k in complex_keywords):
        d.complexity = min(10.0, d.complexity + 2.0)
    urgent_keywords = ["urgent", "maintenant", "prod", "client attend", "critique"]
    if any(k in desc_lower for k in urgent_keywords):
        d.stakes = min(10.0, d.stakes + 2.0)
        d.speed_need = max(1.0, d.speed_need - 3.0)
    return d


def score_and_route(description: str, task_type: TaskType = TaskType.QUICK,
                    dimensions: Optional[ScoringDimensions] = None) -> TaskAssignment:
    log.info("   🔢 SCORING — type: %s", task_type.value)
    if dimensions is None:
        dimensions = infer_dimensions(description, task_type)
    score = calculate_score(dimensions)
    model = select_model(score, dimensions)
    agent = select_agent(description, task_type)
    log.info("   🔢 Dimensions: cx=%s st=%s cr=%s sp=%s dm=%s", dimensions.complexity, dimensions.stakes, dimensions.creativity, dimensions.speed_need, dimensions.domain_match)
    log.info("   🔢 Score: %s | Modèle: %s | Agent: %s", round(score, 2), model.value, agent.value)

    subtasks = []
    # DAG Subtask Decomposition for complex tasks (complexity >= 7.0)
    if dimensions.complexity >= 7.0:
        subtasks = [
            TaskAssignment(
                task_id=f"T_{uuid.uuid4().hex[:4].upper()}_1",
                description=f"Phase 1 - Spécification et Architecture: {description[:60]}",
                agent=AgentName.ARCHITECT,
                model=ModelName.BEST,
                score=round(score, 2),
                dimensions=dimensions,
                subtasks=[],
            ),
            TaskAssignment(
                task_id=f"T_{uuid.uuid4().hex[:4].upper()}_2",
                description=f"Phase 2 - Implémentation et Tests: {description[:60]}",
                agent=AgentName.CODER if agent != AgentName.CODER else AgentName.DEBUGGER,
                model=model,
                score=round(score * 0.9, 2),
                dimensions=dimensions,
                subtasks=[],
            ),
        ]

    return TaskAssignment(
        task_id=f"T_{uuid.uuid4().hex[:6].upper()}",
        description=description,
        agent=agent,
        model=model,
        score=round(score, 2),
        dimensions=dimensions,
        subtasks=subtasks,
    )

