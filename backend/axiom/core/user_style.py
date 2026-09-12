"""
AXIOM v4.0 — Adaptation Style Utilisateur
Détection automatique : EXPERT_TECHNIQUE, DÉVELOPPEUR_INTERMÉDIAIRE, FONDATEUR_NON_TECHNIQUE, ÉTUDIANT_APPRENANT
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from axiom.core.memory import MemoryManager


class UserStyle(str, Enum):
    EXPERT_TECHNIQUE = "EXPERT_TECHNIQUE"
    DEVELOPPEUR_INTERMEDIAIRE = "DEVELOPPEUR_INTERMEDIAIRE"
    FONDATEUR_NON_TECHNIQUE = "FONDATEUR_NON_TECHNIQUE"
    ETUDIANT_APPRENANT = "ETUDIANT_APPRENANT"


@dataclass
class StyleConfig:
    name: UserStyle
    description: str
    # Vocabulaire
    use_technical_jargon: bool = True
    explain_concepts: bool = False
    use_metaphors: bool = False
    # Structure
    show_code_without_basics: bool = True
    show_executive_summary: bool = False
    show_step_by_step: bool = False
    # Optimisations
    propose_advanced_opts: bool = False
    warn_common_pitfalls: bool = False
    encourage: bool = False
    suggest_resources: bool = False
    # Format
    prefer_files_over_inline: bool = True
    max_explanation_length: int = 0  # 0 = illimité


STYLE_CONFIGS: Dict[UserStyle, StyleConfig] = {
    UserStyle.EXPERT_TECHNIQUE: StyleConfig(
        name=UserStyle.EXPERT_TECHNIQUE,
        description="Vocabulaire technique sans vulgarisation, code sans explications basiques",
        use_technical_jargon=True,
        explain_concepts=False,
        use_metaphors=False,
        show_code_without_basics=True,
        show_executive_summary=False,
        show_step_by_step=False,
        propose_advanced_opts=True,
        warn_common_pitfalls=False,
        encourage=False,
        suggest_resources=False,
        prefer_files_over_inline=True,
        max_explanation_length=0,
    ),
    UserStyle.DEVELOPPEUR_INTERMEDIAIRE: StyleConfig(
        name=UserStyle.DEVELOPPEUR_INTERMEDIAIRE,
        description="Expliquer choix non-évidents, commenter points clés, signaler pièges",
        use_technical_jargon=True,
        explain_concepts=True,  # pour concepts non-évidents
        use_metaphors=False,
        show_code_without_basics=True,
        show_executive_summary=False,
        show_step_by_step=False,
        propose_advanced_opts=True,
        warn_common_pitfalls=True,
        encourage=False,
        suggest_resources=False,
        prefer_files_over_inline=True,
        max_explanation_length=0,
    ),
    UserStyle.FONDATEUR_NON_TECHNIQUE: StyleConfig(
        name=UserStyle.FONDATEUR_NON_TECHNIQUE,
        description="Métaphores/analogies, focus business, résumés exécutifs, trade-offs clairs",
        use_technical_jargon=False,
        explain_concepts=True,
        use_metaphors=True,
        show_code_without_basics=False,
        show_executive_summary=True,
        show_step_by_step=True,
        propose_advanced_opts=False,
        warn_common_pitfalls=False,
        encourage=True,
        suggest_resources=True,
        prefer_files_over_inline=False,
        max_explanation_length=200,
    ),
    UserStyle.ETUDIANT_APPRENANT: StyleConfig(
        name=UserStyle.ETUDIANT_APPRENANT,
        description="Explications paso-a-paso, raisons derrière décisions, encouragements, ressources",
        use_technical_jargon=False,
        explain_concepts=True,
        use_metaphors=True,
        show_code_without_basics=False,
        show_executive_summary=False,
        show_step_by_step=True,
        propose_advanced_opts=False,
        warn_common_pitfalls=True,
        encourage=True,
        suggest_resources=True,
        prefer_files_over_inline=True,
        max_explanation_length=500,
    ),
}


# Signaux de détection par style
STYLE_DETECTION_SIGNALS = {
    UserStyle.EXPERT_TECHNIQUE: {
        "keywords": [
            "architecture", "design pattern", "scalable", "microservices", "concurrency",
            "race condition", "deadlock", "optimisation", "profiling", "benchmark",
            "dependency injection", "inversion of control", "solid", "clean architecture",
            "event sourcing", "cqrs", "kafka", "redis", "postgresql", "kubernetes",
            "docker", "ci/cd", "terraform", "ansible", "observability", "tracing",
        ],
        "question_patterns": [
            "comment optimiser", "quelle architecture", "trade-off", "comparer",
            "best practice", "performance", "latence", "throughput",
        ],
        "reaction_signals": {
            "too_verbose": -2,
            "too_simple": +2,
            "wants_code_only": +3,
        },
    },
    UserStyle.DEVELOPPEUR_INTERMEDIAIRE: {
        "keywords": [
            "comment faire", "comment implémenter", "exemple", "tutoriel", "guide",
            "erreur", "bug", "ne marche pas", "stack trace", "exception",
            "library", "package", "import", "install", "configuration",
            "test", "mock", "fixture", "pytest", "jest", "vitest",
        ],
        "question_patterns": [
            "comment", "pourquoi", "quelle est la différence", "vs", "versus",
            "meilleure façon", "best way", "recommande",
        ],
        "reaction_signals": {
            "too_verbose": -1,
            "too_simple": 0,
            "wants_explanation": +2,
            "asks_followup": +1,
        },
    },
    UserStyle.FONDATEUR_NON_TECHNIQUE: {
        "keywords": [
            "business", "roi", "coût", "budget", "délai", "livraison", "client",
            "marché", "produit", "fonctionnalité", "feature", "mvp", "prototype",
            "investisseur", "funding", "équipe", "recrutement", "roadmap",
        ],
        "question_patterns": [
            "combien", "quel budget", "combien de temps", "quand",
            "impact", "valeur", "risque", "alternative", "option",
        ],
        "reaction_signals": {
            "too_technical": -3,
            "wants_business_focus": +3,
            "asks_for_summary": +2,
            "confused_by_jargon": -2,
        },
    },
    UserStyle.ETUDIANT_APPRENANT: {
        "keywords": [
            "apprendre", "comprendre", "cours", "exercice", "devoir", "projet école",
            "débutant", "novice", "bases", "fondamentaux", "pas à pas",
            "pourquoi", "comment ça marche", "explique", "détail",
        ],
        "question_patterns": [
            "c'est quoi", "qu'est-ce que", "pourquoi", "comment",
            "peux-tu m'expliquer", "je ne comprends pas",
        ],
        "reaction_signals": {
            "too_technical": -2,
            "wants_step_by_step": +3,
            "thanks_explanation": +2,
            "asks_for_resources": +2,
        },
    },
}


class UserStyleDetector:
    """
    Détecte et adapte automatiquement le style utilisateur.
    Utilise: mots-clés, patterns de questions, réactions, historique, déclaration explicite.
    """

    def __init__(self, memory: Optional[MemoryManager] = None):
        self.memory = memory
        self._detected_style: Optional[UserStyle] = None
        self._confidence: float = 0.0
        self._signal_scores: Dict[UserStyle, float] = {s: 0.0 for s in UserStyle}
        self._interaction_count = 0

    def analyze_input(self, user_input: str) -> Dict[UserStyle, float]:
        """Analyse un input utilisateur et met à jour les scores par style."""
        input_lower = user_input.lower()
        scores = {s: 0.0 for s in UserStyle}

        for style, signals in STYLE_DETECTION_SIGNALS.items():
            # Mots-clés
            for kw in signals["keywords"]:
                if kw.lower() in input_lower:
                    scores[style] += 1.0

            # Patterns de questions
            for pattern in signals["question_patterns"]:
                if pattern.lower() in input_lower:
                    scores[style] += 1.5

        # Mettre à jour les scores cumulés
        for style, score in scores.items():
            self._signal_scores[style] += score

        self._interaction_count += 1
        return scores

    def analyze_reaction(self, reaction: str) -> None:
        """Analyse la réaction de l'utilisateur à une réponse précédente."""
        reaction_lower = reaction.lower()

        for style, signals in STYLE_DETECTION_SIGNALS.items():
            for signal, weight in signals["reaction_signals"].items():
                if signal in reaction_lower:
                    self._signal_scores[style] += weight

    def detect_style(self, explicit_declaration: Optional[str] = None) -> UserStyle:
        """
        Détecte le style utilisateur.
        Si declaration_explicite fournie, l'utilise directement.
        Sinon, calcule basé sur les signaux accumulés.
        """
        if explicit_declaration:
            explicit_lower = explicit_declaration.lower()
            # Check more specific patterns first
            if "fondateur" in explicit_lower or "non-technique" in explicit_lower or "non technique" in explicit_lower or "business" in explicit_lower:
                self._detected_style = UserStyle.FONDATEUR_NON_TECHNIQUE
                self._confidence = 1.0
                return self._detected_style
            if "étudiant" in explicit_lower or "etudiant" in explicit_lower or "apprenant" in explicit_lower or "débutant" in explicit_lower or "debutant" in explicit_lower:
                self._detected_style = UserStyle.ETUDIANT_APPRENANT
                self._confidence = 1.0
                return self._detected_style
            if "expert" in explicit_lower or "technique" in explicit_lower:
                self._detected_style = UserStyle.EXPERT_TECHNIQUE
                self._confidence = 1.0
                return self._detected_style
            if "dev" in explicit_lower or "développeur" in explicit_lower or "intermédiaire" in explicit_lower or "intermediaire" in explicit_lower:
                self._detected_style = UserStyle.DEVELOPPEUR_INTERMEDIAIRE
                self._confidence = 1.0
                return self._detected_style

        # Calculer le style basé sur les scores accumulés
        if self._interaction_count >= 3:  # Minimum d'interactions
            best_style = max(self._signal_scores, key=self._signal_scores.get)
            max_score = self._signal_scores[best_style]
            total_score = sum(max(0, s) for s in self._signal_scores.values())

            if total_score > 0:
                self._confidence = max_score / total_score
                if self._confidence > 0.3:  # Seuil de confiance
                    self._detected_style = best_style
                    return best_style

        # Défaut: développeur intermédiaire
        self._detected_style = UserStyle.DEVELOPPEUR_INTERMEDIAIRE
        self._confidence = 0.5
        return self._detected_style

    def get_current_style(self) -> UserStyle:
        """Retourne le style actuel détecté."""
        if self._detected_style is None:
            return self.detect_style()
        return self._detected_style

    def get_style_config(self) -> StyleConfig:
        """Retourne la config du style actuel."""
        return STYLE_CONFIGS[self.get_current_style()]

    def get_confidence(self) -> float:
        return self._confidence

    def get_all_scores(self) -> Dict[UserStyle, float]:
        return self._signal_scores.copy()

    def reset(self):
        """Remet à zéro la détection."""
        self._detected_style = None
        self._confidence = 0.0
        self._signal_scores = {s: 0.0 for s in UserStyle}
        self._interaction_count = 0

    def load_from_memory(self) -> None:
        """Charge le style depuis la mémoire épisodique si disponible."""
        if self.memory:
            episodic = self.memory.get_episodic()
            user_prefs = episodic.user
            if user_prefs.get("style_communication"):
                style_str = user_prefs["style_communication"]
                try:
                    self._detected_style = UserStyle(style_str)
                    self._confidence = 0.9
                except ValueError:
                    pass

    def save_to_memory(self) -> None:
        """Sauvegarde le style détecté en mémoire épisodique."""
        if self.memory and self._detected_style:
            episodic = self.memory.get_episodic()
            episodic.user["style_communication"] = self._detected_style.value
            episodic.user["niveau_technique"] = self._style_to_niveau(self._detected_style)
            episodic.user["langue"] = "FR"

    def _style_to_niveau(self, style: UserStyle) -> str:
        mapping = {
            UserStyle.EXPERT_TECHNIQUE: "expert",
            UserStyle.DEVELOPPEUR_INTERMEDIAIRE: "intermédiaire",
            UserStyle.FONDATEUR_NON_TECHNIQUE: "non-technique",
            UserStyle.ETUDIANT_APPRENANT: "débutant",
        }
        return mapping.get(style, "intermédiaire")


def apply_style_to_prompt(
    base_prompt: str,
    style: UserStyle,
    task_description: str = "",
) -> str:
    """Applique l'adaptation de style à un prompt."""
    config = STYLE_CONFIGS[style]

    style_instructions = []

    if style == UserStyle.EXPERT_TECHNIQUE:
        style_instructions.append(
            "STYLE: EXPERT_TECHNIQUE — Vocabulaire technique pur, pas de vulgarisation. "
            "Code sans explications basiques. Aller droit au problème. "
            "Proposer optimisations avancées spontanément."
        )
    elif style == UserStyle.DEVELOPPEUR_INTERMEDIAIRE:
        style_instructions.append(
            "STYLE: DÉVELOPPEUR_INTERMÉDIAIRE — Expliquer choix techniques non-évidents. "
            "Commenter code aux points clés. Signaler pièges courants. "
            "Pas de vulgarisation excessive."
        )
    elif style == UserStyle.FONDATEUR_NON_TECHNIQUE:
        style_instructions.append(
            "STYLE: FONDATEUR_NON_TECHNIQUE — Métaphores/analogies pour concepts tech. "
            "Focus impact business, pas implémentation. Résumés exécutifs avant détails. "
            "Options présentées avec trade-offs clairs."
        )
    elif style == UserStyle.ETUDIANT_APPRENANT:
        style_instructions.append(
            "STYLE: ÉTUDIANT_APPRENANT — Explications paso-a-paso. "
            "Raisons derrière chaque décision. Encouragements mesurés. "
            "Proposer ressources complémentaires."
        )

    if style_instructions:
        return f"{base_prompt}\n\n{' '.join(style_instructions)}"
    return base_prompt


def format_response_for_style(
    content: str,
    style: UserStyle,
    agent_name: str = "",
    model_name: str = "",
) -> str:
    """Formate la réponse selon le style utilisateur."""
    config = STYLE_CONFIGS[style]

    # Pour fondateur: ajouter résumé exécutif si pas déjà là
    if style == UserStyle.FONDATEUR_NON_TECHNIQUE and config.show_executive_summary:
        if not content.startswith("## Résumé"):
            # Extraire les points clés (première phrase de chaque paragraphe)
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            if len(paragraphs) > 1:
                executive = "## Résumé Exécutif\n" + "\n".join(
                    f"- {p.split('.')[0]}" for p in paragraphs[:3]
                ) + "\n\n---\n\n"
                content = executive + content

    # Pour étudiant: ajouter encouragements
    if style == UserStyle.ETUDIANT_APPRENANT and config.encourage:
        if not "💡" in content and not "🎯" in content:
            content += "\n\n💡 **Continuez comme ça !** Chaque question vous fait progresser."

    return content