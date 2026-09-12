"""
Prompt Builder for APEX v4.0

Ce module est responsable de la construction des prompts système et utilisateur
pour les différentes étapes de la boucle ReAct.

Il gère:
- Les templates de prompts par agent
- L'injection du contexte et des dimensions
- L'adaptation selon le mode opérationnel
- L'application du style utilisateur
"""

from typing import Optional, Dict
from axiom.models.schemas import TaskAssignment, AgentName
from axiom.core.operation_modes import OperationMode, MODE_CONFIGS
from axiom.core.user_style import apply_style_to_prompt
from axiom.core.system_prompt import HAKIM_SYSTEM_PROMPT


# =============================================================================
# ICÔNES ET INSTRUCTIONS PAR AGENT
# =============================================================================

AGENT_ICONS: Dict[str, str] = {
    "AGENT_ARCHITECT": "🏗️",
    "AGENT_CODER": "💻",
    "AGENT_DEBUGGER": "🐛",
    "AGENT_ANALYST": "📊",
    "AGENT_WRITER": "✍️",
    "AGENT_RESEARCHER": "🔍",
    "AGENT_PLANNER": "🎯",
    "AGENT_QUICKSHOT": "⚡",
}

AGENT_INSTRUCTIONS: Dict[str, str] = {
    "AGENT_ARCHITECT": """
SPÉCIALITÉ: Architecture système, design patterns, ADR, choix techniques
APPROCHE: Chain-of-Thought + First Principles
LIVRABLES: Diagrammes Mermaid, ADR, comparaisons patterns avec trade-offs, roadmap technique
""",
    "AGENT_CODER": """
SPÉCIALITÉ: Génération, refactoring, optimisation de code
APPROCHE: Think-before-code (plan → implement → review)
LIVRABLES: Code complet, testé, commenté, types TypeScript/Python, gestion erreurs robuste, tests unitaires
""",
    "AGENT_DEBUGGER": """
SPÉCIALITÉ: Debug, root-cause analysis, corrections
APPROCHE: Reproduce → Isolate → Hypothesize → Verify → Fix
LIVRABLES: Root cause documentée, fix minimal (pas de refactoring inutile), explication pourquoi, prévention future
""",
    "AGENT_ANALYST": """
SPÉCIALITÉ: Data, SQL, statistiques, visualisation, insights
APPROCHE: Explore → Hypothesize → Validate → Communicate
LIVRABLES: Insights actionnables (pas juste chiffres), code Python/SQL prêt emploi, visualisations (matplotlib/recharts/d3), recommandations data-driven
""",
    "AGENT_WRITER": """
SPÉCIALITÉ: Rédaction, documentation, contenu, communication
APPROCHE: Audience → Message → Tone → Structure → Draft → Polish
LIVRABLES: Contenu prêt à publier/envoyer, ton adapté au contexte, plusieurs versions si besoin (formel/casual), format adapté au medium
""",
    "AGENT_RESEARCHER": """
SPÉCIALITÉ: Recherche web, veille, fact-checking, comparaisons
APPROCHE: Query → Multi-source → Cross-verify → Synthesize
LIVRABLES: Information vérifiée et citée, synthèse structurée, sources identifiées, date dernière mise à jour
""",
    "AGENT_PLANNER": """
SPÉCIALITÉ: Planification, stratégie, roadmaps, cahiers des charges
APPROCHE: Goals → Constraints → Decompose → Prioritize → Schedule
LIVRABLES: Plan structuré étapes/dépendances/délais, matrice priorisation impact/effort, risques + mitigation, métriques succès
""",
    "AGENT_QUICKSHOT": """
SPÉCIALITÉ: Réponses rapides, extraction, classification, reformulation
APPROCHE: Direct → Concise → Done
LIVRABLES: Réponse directe minimale immédiate, données structurées (JSON/CSV), résumé bullet-point si liste
""",
}

# Règles spécifiques par itération
ITERATION_RULES = """
RÈGLES SPÉCIFIQUES CETTE ITÉRATION:
- Format de réponse STANDARD APEX obligatoire (icône, séparateurs, ✅/⚠️/⏭️)
- ZÉRO filler, direct et dense
- Si code: types, gestion erreurs, tests inclus
- Si doc: Markdown structuré avec TOC si >3 sections
- Ne jamais halluciner APIs
"""


class PromptBuilder:
    """
    Constructeur de prompts pour la boucle ReAct.
    
    Responsabilités:
    - Construction du prompt système avec contexte agent
    - Construction du prompt utilisateur avec contexte tâche
    - Injection des dimensions de scoring
    - Adaptation selon le mode opérationnel
    - Application du style utilisateur
    """
    
    def __init__(self, user_style_detector: any = None):
        """
        Initialise le constructeur de prompts.
        
        Args:
            user_style_detector: Détecteur de style utilisateur (optionnel)
        """
        self.user_style_detector = user_style_detector
    
    def build_system_prompt(
        self,
        task: TaskAssignment,
        iteration: int,
        max_iterations: int,
        current_mode: Optional[OperationMode] = None,
    ) -> str:
        """
        Construit le prompt système pour une itération.
        
        Args:
            task: Assignment de tâche
            iteration: Numéro de l'itération (1-based)
            max_iterations: Nombre maximum d'itérations
            current_mode: Mode opérationnel actuel
            
        Returns:
            Prompt système formaté
        """
        # Récupérer l'icône de l'agent
        icon = AGENT_ICONS.get(task.agent.value, "🤖")
        
        # Indicateur de mode
        mode_indicator = f" [MODE: {current_mode.value}]" if current_mode else ""
        
        # Instructions spécifiques à l'agent
        agent_instructions = AGENT_INSTRUCTIONS.get(task.agent.value, "")
        
        # Appliquer le style utilisateur
        style_prompt = ""
        if self.user_style_detector:
            current_style = self.user_style_detector.get_current_style()
            style_prompt = apply_style_to_prompt(
                "", current_style, task.description
            )
        
        # Assembler le prompt
        system_prompt = f"""{HAKIM_SYSTEM_PROMPT}

---
CONTEXTE EXÉCUTION:
Agent: {icon} {task.agent.value}{mode_indicator}
Modèle: {task.model.value}
Score tâche: {task.score}/10
Itération: {iteration}/{max_iterations}

{agent_instructions}

{style_prompt}

{ITERATION_RULES}"""
        
        return system_prompt
    
    def build_user_prompt(
        self,
        task: TaskAssignment,
        context: Optional[str],
        iteration: int,
        max_iterations: int,
        current_mode: Optional[OperationMode] = None,
        dimensions: Optional[any] = None,
    ) -> str:
        """
        Construit le prompt utilisateur pour une itération.
        
        Args:
            task: Assignment de tâche
            context: Contexte supplémentaire
            iteration: Numéro de l'itération
            max_iterations: Nombre maximum d'itérations
            current_mode: Mode opérationnel actuel
            dimensions: Dimensions de scoring
            
        Returns:
            Prompt utilisateur formaté
        """
        parts = [f"TÂCHE: {task.description}"]
        
        if iteration > 1:
            parts.append(f"\nITÉRATION: {iteration}/{max_iterations}")
        
        if context:
            parts.append(f"\nCONTEXTE SUPPLÉMENTAIRE:\n{context}")
        
        # Ajouter les dimensions de scoring
        if dimensions:
            parts.append(f"\nDIMENSIONS SCORING:\n{dimensions.model_dump_json(indent=2)}")
        elif hasattr(task, 'dimensions'):
            parts.append(f"\nDIMENSIONS SCORING:\n{task.dimensions.model_dump_json(indent=2)}")
        
        # Ajouter le mode opérationnel
        mode_text = current_mode.value if current_mode else "AUTONOME"
        parts.append(f"\nMODE OPÉRATION: {mode_text}")
        
        # Ajouter les instructions spécifiques au mode
        if current_mode:
            from axiom.core.operation_modes import MODE_CONFIGS
            config = MODE_CONFIGS[current_mode]
            parts.append(f"\nCOMPORTEMENT MODE {current_mode.value}: {config.behavior_notes}")
        
        parts.append("\nProduis le résultat complet directement. Format réponse standard APEX requis.")
        
        return "\n".join(parts)
    
    def build_self_critique_prompt(
        self,
        task_description: str,
        output: str,
        agent: AgentName,
        model: any,
        iteration: int,
        max_iterations: int,
        dimensions: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        Construit le prompt pour l'auto-critique.
        
        Args:
            task_description: Description de la tâche
            output: Sortie générée par le LLM
            agent: Agent utilisé
            model: Modèle utilisé
            iteration: Itération actuelle
            max_iterations: Nombre maximum d'itérations
            dimensions: Dimensions de scoring
            
        Returns:
            Prompt d'auto-critique formaté
        """
        from axiom.core.system_prompt import build_self_critique_prompt
        return build_self_critique_prompt(
            task_description=task_description,
            output=output,
            agent=agent,
            model=model,
            iteration=iteration,
            max_iterations=max_iterations,
            dimensions=dimensions or {},
        )
