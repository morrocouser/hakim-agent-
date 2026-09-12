from axiom.models.schemas import (
    ScoringDimensions, ScoringWeights, ModelName, AgentName,
    TaskType, TaskAssignment,
)
from axiom.logging_setup import log
from typing import Optional
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


def select_model(score: float, dimensions: ScoringDimensions) -> ModelName:
    if dimensions.stakes >= 9:
        return ModelName.BEST
    if dimensions.speed_need <= 3 and score > 6:
        return URGENT_OVERRIDE
    for low, high, model in MODEL_THRESHOLDS:
        if low <= score <= high:
            return model
    return ModelName.BEST


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

