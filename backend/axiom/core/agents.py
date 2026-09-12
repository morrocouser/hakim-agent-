from axiom.models.schemas import AgentName, ModelName
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    name: AgentName
    label: str
    icon: str
    default_model: ModelName
    speciality: str
    description: str
    approach: str
    skills: list[str] = field(default_factory=list)


AGENT_CONFIGS: dict[AgentName, AgentConfig] = {
    AgentName.ARCHITECT: AgentConfig(
        name=AgentName.ARCHITECT,
        label="Architecte Système",
        icon="🏗️",
        default_model=ModelName.BEST,
        speciality="Architecture système, design patterns, ADR, choix techniques",
        description="Conçoit l'architecture macro des systèmes, rédige des ADR, compare des patterns",
        approach="Chain-of-Thought + First Principles",
        skills=["Architecture Design", "RAG", "Dependency Analysis", "System Design", "MCP"],
    ),
    AgentName.CODER: AgentConfig(
        name=AgentName.CODER,
        label="Développeur",
        icon="💻",
        default_model=ModelName.LARGE,
        speciality="Génération, refactoring, optimisation de code",
        description="Génère du code complet, testé, avec gestion d'erreurs et types",
        approach="Think-before-code (plan → implement → review)",
        skills=["Code Generation", "Refactoring", "Test Generation", "TypeScript", "React", "Next.js", "Tailwind", "FastAPI", "Find Skills"],
    ),
    AgentName.DEBUGGER: AgentConfig(
        name=AgentName.DEBUGGER,
        label="Débugger",
        icon="🐛",
        default_model=ModelName.BEST,
        speciality="Debug, root-cause analysis, corrections",
        description="Analyse les causes racines et applique des fixes minimaux",
        approach="Reproduce → Isolate → Hypothesize → Verify → Fix",
        skills=["Debugging", "Security Review", "Diff Generator", "File Search", "Project Analyzer"],
    ),
    AgentName.ANALYST: AgentConfig(
        name=AgentName.ANALYST,
        label="Analyste",
        icon="📊",
        default_model=ModelName.LARGE,
        speciality="Data, SQL, statistiques, visualisation, insights",
        description="Analyse les données, produit des insights actionnables et des visualisations",
        approach="Explore → Hypothesize → Validate → Communicate",
        skills=["SQL", "Data Cleaning", "Performance Optimization", "PostgreSQL", "CSV", "JSON"],
    ),
    AgentName.WRITER: AgentConfig(
        name=AgentName.WRITER,
        label="Rédacteur",
        icon="✍️",
        default_model=ModelName.MEDIUM,
        speciality="Rédaction, documentation, contenu, communication",
        description="Rédige du contenu prêt à publier avec ton adapté au contexte",
        approach="Audience → Message → Tone → Structure → Draft → Polish",
        skills=["Documentation Generator", "Markdown", "Prompt Engineering"],
    ),
    AgentName.RESEARCHER: AgentConfig(
        name=AgentName.RESEARCHER,
        label="Chercheur",
        icon="🔍",
        default_model=ModelName.LARGE,
        speciality="Recherche web, veille, fact-checking, comparaisons",
        description="Recherche et vérifie l'information, produit des synthèses structurées",
        approach="Query → Multi-source → Cross-verify → Synthesize",
        skills=["Web Search", "Deep Research", "Documentation Search", "Semantic Search", "GitHub Search", "Find Skills"],
    ),
    AgentName.PLANNER: AgentConfig(
        name=AgentName.PLANNER,
        label="Planificateur",
        icon="🎯",
        default_model=ModelName.BEST,
        speciality="Planification, stratégie, roadmaps, cahiers des charges",
        description="Décompose les projets complexes en plans structurés avec priorités",
        approach="Goals → Constraints → Decompose → Prioritize → Schedule",
        skills=["Planner", "Goal Manager", "Workflow Engine", "Task Manager", "State Manager", "Find Skills"],
    ),
    AgentName.QUICKSHOT: AgentConfig(
        name=AgentName.QUICKSHOT,
        label="Réponse Rapide",
        icon="⚡",
        default_model=ModelName.SMALL,
        speciality="Réponses rapides, extraction, classification, reformulation",
        description="Répond directement et immédiatement aux questions simples",
        approach="Direct → Concise → Done",
        skills=["Prompt Engineering", "Tool Calling", "File Reader"],
    ),
}


def get_agent_config(name: AgentName) -> AgentConfig:
    return AGENT_CONFIGS[name]


def get_default_model(agent: AgentName) -> ModelName:
    return AGENT_CONFIGS[agent].default_model


def get_agent_icon(agent: AgentName) -> str:
    return AGENT_CONFIGS[agent].icon
