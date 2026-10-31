"""
AXIOM v4.0 — Système de Modes d'Opération
7 modes : AUTONOME, COLLABORATIF, DEBUG, URGENCE, RECHERCHE, DOCUMENTATION, ITÉRATIF
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from axiom.models.schemas import TaskType, AgentName, ModelName, ScoringDimensions


class OperationMode(str, Enum):
    AUTONOME = "AUTONOME"
    COLLABORATIF = "COLLABORATIF"
    DEBUG = "DEBUG"
    URGENCE = "URGENCE"
    RECHERCHE = "RECHERCHE"
    DOCUMENTATION = "DOCUMENTATION"
    ITERATIF = "ITERATIF"


@dataclass
class ModeConfig:
    name: OperationMode
    description: str
    triggers: List[str]
    requires_confirmation: bool = False
    max_iterations: int = 3
    model_override: Optional[ModelName] = None
    score_speed_adjustment: int = 0
    behavior_notes: str = ""

    # Pour modes qui présentent des alternatives
    present_alternatives: bool = False
    max_alternatives: int = 3


MODE_CONFIGS: Dict[OperationMode, ModeConfig] = {
    OperationMode.AUTONOME: ModeConfig(
        name=OperationMode.AUTONOME,
        description="Exécution automatique sans confirmation, livraison directe avec résumé",
        triggers=["tâche claire", "sans ambiguïté", "risque faible"],
        requires_confirmation=False,
        max_iterations=3,
        behavior_notes="Livre avec résumé 2 lignes + propose 1-2 prochaines étapes",
    ),
    OperationMode.COLLABORATIF: ModeConfig(
        name=OperationMode.COLLABORATIF,
        description="Plan présenté avant exécution, validation pour étapes irréversibles",
        triggers=["tâche ambiguë", "enjeux élevés", "stakes >= 8"],
        requires_confirmation=True,
        max_iterations=3,
        present_alternatives=True,
        max_alternatives=3,
        behavior_notes="Présente plan 3-5 étapes + 2-3 alternatives avec trade-offs",
    ),
    OperationMode.DEBUG: ModeConfig(
        name=OperationMode.DEBUG,
        description="Mode debug: Reproduce → Isolate → Hypothesize → Fix → Prevent",
        triggers=["bug", "erreur", "comportement inattendu", "tests échouent"],
        requires_confirmation=False,
        max_iterations=3,
        behavior_notes="Fix minimal seulement, pas de refactoring. Documente leçon dans ERROR_LOG",
    ),
    OperationMode.URGENCE: ModeConfig(
        name=OperationMode.URGENCE,
        description="Livraison résultat en premier, détails après si demandés",
        triggers=["prod", "urgent", "maintenant", "client attend"],
        requires_confirmation=False,
        max_iterations=2,
        score_speed_adjustment=-1,
        behavior_notes="Réponse directe et concise sans fioritures",
    ),
    OperationMode.RECHERCHE: ModeConfig(
        name=OperationMode.RECHERCHE,
        description="Recherche web systématique, sources citées, date vérification",
        triggers=["actualité", "technologies récentes", "prix", "événements", "comparatif"],
        requires_confirmation=False,
        max_iterations=2,
        behavior_notes="web_search obligatoire avant réponse. Sources citées + date dernière vérif",
    ),
    OperationMode.DOCUMENTATION: ModeConfig(
        name=OperationMode.DOCUMENTATION,
        description="Format Markdown structuré, table des matières, livrables fichiers",
        triggers=["documente", "readme", "cahier des charges", "specs", "documentation"],
        requires_confirmation=False,
        max_iterations=2,
        behavior_notes="Format MD structuré, TOC si >3 sections, fichiers pas inline",
    ),
    OperationMode.ITERATIF: ModeConfig(
        name=OperationMode.ITERATIF,
        description="Amélioration incrémentale: charge dernier résultat, applique changements demandés",
        triggers=["améliore", "raffine", "v2", "encore", "itère", "optimise"],
        requires_confirmation=False,
        max_iterations=5,
        behavior_notes="Charge dernier résultat mémoire, conserve ce qui marchait, applique delta",
    ),
}


def detect_operation_mode(
    user_input: str,
    task_type: TaskType,
    dimensions: ScoringDimensions,
    memory_context: Optional[str] = None
) -> OperationMode:
    """
    Détecte le mode d'opération approprié basé sur:
    - Mots-clés dans l'input utilisateur
    - Type de tâche
    - Dimensions de scoring
    - Contexte mémoire (mode précédent si ITERATIF)
    """
    input_lower = user_input.lower()

    # Mots-clés forts pour chaque mode
    mode_keywords = {
        OperationMode.DEBUG: [
            "bug", "erreur", "exception", "crash", "ne marche pas",
            "ne fonctionne pas", "cassé", "problème", "debug", "débog",
            "stack trace", "traceback", "failed", "échec", "test échoue"
        ],
        OperationMode.URGENCE: [
            "urgent", "maintenant", "tout de suite", "immédiat", "prod",
            "production", "client attend", "deadline", "asap", "vite",
            "rapide", "presse", "critique"
        ],
        OperationMode.RECHERCHE: [
            "recherche", "actualité", "récent", "dernier", "nouveau",
            "prix", "coût", "tarif", "disponible", "sortie", "version",
            "compar", "vs", "versus", "quelle est la meilleure", "best",
            "alternative à", "remplace", "veilles", "news"
        ],
        OperationMode.DOCUMENTATION: [
            "documente", "documentation", "readme", "cahier des charges",
            "specs", "spécifications", "manuel", "guide", "tutoriel",
            "wiki", "changelog", "api doc", "commentaire"
        ],
        OperationMode.ITERATIF: [
            "améliore", "ameliore", "raffine", "optimise", "v2", "v3",
            "version 2", "version 3", "encore", "itère", "refais",
            "reprends", "continue", "ajoute", "modifie", "change"
        ],
        OperationMode.COLLABORATIF: [
            "aide-moi à décider", "choisis", "quelle option", "que ferais-tu",
            "conseille", "recommande", "compare", "trade-off", "avantages",
            "inconvénients", "planifie", "stratégie", "roadmap"
        ],
    }

    # Vérification mots-clés (ordre de priorité)
    priority_order = [
        OperationMode.DEBUG,
        OperationMode.URGENCE,
        OperationMode.RECHERCHE,
        OperationMode.DOCUMENTATION,
        OperationMode.ITERATIF,
        OperationMode.COLLABORATIF,
    ]

    for mode in priority_order:
        keywords = mode_keywords.get(mode, [])
        if any(kw in input_lower for kw in keywords):
            return mode

    # Détection par dimensions de scoring
    if dimensions.stakes >= 8:
        return OperationMode.COLLABORATIF

    if dimensions.speed_need <= 2:
        return OperationMode.URGENCE

    # Détection par type de tâche
    task_type_mode_map = {
        TaskType.DEBUG: OperationMode.DEBUG,
        TaskType.RESEARCH: OperationMode.RECHERCHE,
        TaskType.DOC: OperationMode.DOCUMENTATION,
        TaskType.PLAN: OperationMode.COLLABORATIF,
        TaskType.WEB: OperationMode.AUTONOME,
    }

    if task_type in task_type_mode_map:
        return task_type_mode_map[task_type]

    # Mode par défaut
    return OperationMode.AUTONOME


def get_mode_config(mode: OperationMode) -> ModeConfig:
    return MODE_CONFIGS[mode]


def apply_mode_behavior(
    mode: OperationMode,
    task_assignment,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Applique le comportement spécifique au mode sur l'assignation de tâche.
    Retourne les modifications à appliquer.
    """
    config = MODE_CONFIGS[mode]
    modifications = {
        "max_iterations": config.max_iterations,
        "requires_confirmation": config.requires_confirmation,
        "present_alternatives": config.present_alternatives,
        "max_alternatives": config.max_alternatives,
        "behavior_notes": config.behavior_notes,
    }

    # Override modèle si spécifié (URGENCE)
    if config.model_override:
        modifications["model_override"] = config.model_override

    # Ajustement score vitesse (URGENCE)
    if config.score_speed_adjustment != 0:
        modifications["speed_adjustment"] = config.score_speed_adjustment

    # Mode RECHERCHE: forcer web_search
    if mode == OperationMode.RECHERCHE:
        modifications["force_web_search"] = True

    # Mode DOCUMENTATION: forcer format fichier
    if mode == OperationMode.DOCUMENTATION:
        modifications["force_file_output"] = True
        modifications["markdown_format"] = True

    # Mode DEBUG: forcer agent DEBUGGER
    if mode == OperationMode.DEBUG:
        modifications["force_agent"] = "AGENT_DEBUGGER"
        modifications["minimal_fix_only"] = True

    # Mode ITERATIF: charger dernier résultat
    if mode == OperationMode.ITERATIF:
        modifications["load_previous_result"] = True

    return modifications


def format_mode_indicator(mode: OperationMode) -> str:
    """Retourne l'indicateur visuel du mode pour l'affichage."""
    indicators = {
        OperationMode.AUTONOME: "🤖 AUTONOME",
        OperationMode.COLLABORATIF: "🤝 COLLABORATIF",
        OperationMode.DEBUG: "🔬 DEBUG",
        OperationMode.URGENCE: "🏃 URGENCE",
        OperationMode.RECHERCHE: "🧪 RECHERCHE",
        OperationMode.DOCUMENTATION: "📚 DOCUMENTATION",
        OperationMode.ITERATIF: "🔁 ITÉRATIF",
    }
    return indicators.get(mode, mode.value)