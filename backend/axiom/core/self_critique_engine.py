"""
Self-Critique Engine for APEX v4.0

Ce module est responsable de l'auto-évaluation des sorties générées
par les agents IA. Il gère:
- La grille d'évaluation 5 dimensions
- Le calcul des scores et la décision d'itération
- L'extraction des points forts/faibles et améliorations
- Le fallback en cas d'échec de l'évaluation
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from axiom.models.schemas import TaskAssignment, AgentName, ModelName
from axiom.core.system_prompt import build_self_critique_prompt
from axiom.logging_setup import log
import json


# =============================================================================
# TYPES POUR L'AUTO-CRITIQUE
# =============================================================================

class CritiqueScores(BaseModel):
    """Scores pour les différentes dimensions de la critique."""
    pertinence: float = Field(default=5.0, ge=0, le=10)
    complete: float = Field(default=5.0, ge=0, le=10)
    exactitude: float = Field(default=5.0, ge=0, le=10)
    qualite: float = Field(default=5.0, ge=0, le=10)
    concision: float = Field(default=5.0, ge=0, le=10)


class SelfCritiqueResult(BaseModel):
    """Résultat de l'auto-critique."""
    scores: CritiqueScores = Field(default_factory=CritiqueScores)
    score_global: float = Field(default=5.0, ge=0, le=10)
    decision: str = Field(default="LIVRAISON")
    points_forts: List[str] = Field(default_factory=list)
    points_faibles: List[str] = Field(default_factory=list)
    ameliorations_concretes: List[str] = Field(default_factory=list)
    alternative_approche: str = Field(default="")
    
    @classmethod
    def get_default(cls) -> dict:
        """Retourne un résultat par défaut."""
        return {
            "scores": {k: 5.0 for k in ["pertinence", "complete", "exactitude", "qualite", "concision"]},
            "score_global": 5.0,
            "decision": "LIVRAISON",
            "points_forts": [],
            "points_faibles": [],
            "ameliorations_concretes": [],
            "alternative_approche": "",
        }
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire."""
        return {
            "scores": {k: v for k, v in self.scores.model_dump().items()},
            "score_global": self.score_global,
            "decision": self.decision,
            "points_forts": self.points_forts,
            "points_faibles": self.points_faibles,
            "ameliorations_concretes": self.ameliorations_concretes,
            "alternative_approche": self.alternative_approche,
        }


# =============================================================================
# SEUILS DE DÉCISION
# =============================================================================

class DecisionThresholds:
    """Seuils de décision pour l'auto-critique."""
    LIVRAISON_MIN = 8.0
    LIVRAISON_AVERAGE_MIN = 6.0
    ITERATION_MIN = 4.0
    REPLAN_MAX = 4.0


# =============================================================================
# MOTEUR D'AUTO-CRITIQUE
# =============================================================================

class SelfCritiqueEngine:
    """
    Moteur d'auto-critique pour la boucle ReAct.
    
    Responsabilités:
    - Exécution de l'auto-évaluation via LLM
    - Parsing et validation des réponses
    - Calcul des scores et décisions
    - Fallback en cas d'échec
    
    Args:
        claude: Client LLM pour l'évaluation
        thresholds: Configurable thresholds pour les décisions (optionnel)
    """
    
    def __init__(self, claude: any = None, thresholds: Optional[DecisionThresholds] = None):
        """
        Initialise le moteur d'auto-critique.
        
        Args:
            claude: Client LLM (optionnel, pour évaluation dynamique)
            thresholds: Seuils de décision personnalisés
        """
        self.claude = claude
        self.thresholds = thresholds or DecisionThresholds()
    
    async def evaluate(
        self,
        task: TaskAssignment,
        output: str,
        iteration: int,
        max_iterations: int,
    ) -> dict:
        """
        Exécute l'auto-critique complète pour une sortie donnée.
        
        Args:
            task: Assignment de tâche
            output: Sortie générée par le LLM
            iteration: Itération actuelle
            max_iterations: Nombre maximum d'itérations
            
        Returns:
            Dictionnaire avec scores, décision, points forts/faibles, etc.
            
        Raises:
            ValueError: Si impossible de parser la réponse
        """
        # Construire le prompt d'auto-critique
        critique_prompt = build_self_critique_prompt(
            task_description=task.description,
            output=output,
            agent=task.agent,
            model=task.model,
            iteration=iteration,
            max_iterations=max_iterations,
            dimensions=task.dimensions.model_dump(),
        )
        
        # Si pas de client LLM, retourner évaluation par défaut
        if not self.claude:
            log.warning("Pas de client LLM disponible pour l'auto-critique, utilisation fallback")
            return self._fallback_quality_eval(output, task)
        
        try:
            # Appeler le LLM pour l'auto-évaluation
            response = await self.claude.chat(
                model=task.model.value,
                system="Tu es APEX en mode AUTO-ÉVALUATION. Réponds UNIQUEMENT en JSON valide selon le format spécifié.",
                messages=[{"role": "user", "content": critique_prompt}],
                max_tokens=1024,
            )
            
            # Parser et valider la réponse
            result = self._parse_critique_response(response)
            return result
            
        except Exception as e:
            log.warning("Échec auto-critique: %s, utilisation fallback", str(e))
            return self._fallback_quality_eval(output, task)
    
    def _parse_critique_response(self, response: str) -> dict:
        """
        Parse et valide la réponse JSON de l'auto-critique.
        
        Args:
            response: Réponse brute du LLM
            
        Returns:
            Dictionnaire parsé et validé
        """
        # Essayer de parser le JSON
        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            log.warning("Échec parsing JSON auto-critique: %s", str(e))
            log.debug("Réponse brute: %s", response[:500])
            raise ValueError(f"Réponse auto-critique non-JSON valide: {str(e)}")
        
        # Vérifier que c'est un dict
        if not isinstance(result, dict):
            log.warning("Réponse auto-critique n'est pas un dict, type: %s", type(result))
            return SelfCritiqueResult.get_default()
        
        # Si le modèle retourne une string au lieu d'un objet JSON
        if isinstance(result, str):
            return SelfCritiqueResult.get_default()
        
        # Valider les champs requis
        required_scores = ["pertinence", "complete", "exactitude", "qualite", "concision"]
        
        # Initialiser les scores
        if not isinstance(result.get("scores"), dict):
            result["scores"] = {}
        
        for key in required_scores:
            if key not in result["scores"]:
                result["scores"][key] = 5.0
        
        # Calculer le score global si manquant
        if "score_global" not in result:
            scores = result["scores"]
            result["score_global"] = sum(scores.values()) / len(scores)
        
        # Déterminer la décision si manquante
        if "decision" not in result:
            sg = result["score_global"]
            result["decision"] = self._determine_decision(sg)
        
        # Assurer que tous les champs lists existent
        for field in ["points_forts", "points_faibles", "ameliorations_concretes"]:
            if field not in result:
                result[field] = []
        
        if "alternative_approche" not in result:
            result["alternative_approche"] = ""
        
        return result
    
    def _determine_decision(self, score_global: float) -> str:
        """
        Détermine la décision basée sur le score global.
        
        Args:
            score_global: Score global calculé
            
        Returns:
            Décision parmi: LIVRAISON, ITERATION, REPLAN, PARTIEL
        """
        if score_global >= self.thresholds.LIVRAISON_MIN:
            return "LIVRAISON"
        elif score_global >= self.thresholds.LIVRAISON_AVERAGE_MIN:
            return "LIVRAISON"
        elif score_global >= self.thresholds.ITERATION_MIN:
            return "ITERATION"
        else:
            return "REPLAN"
    
    def _fallback_quality_eval(self, output: str, task: TaskAssignment) -> dict:
        """
        Évaluation de qualité de fallback si l'auto-critique échoue.
        
        Args:
            output: Sortie générée
            task: Assignment de tâche
            
        Returns:
            Dictionnaire avec scores par défaut basés sur heuristiques
        """
        score = 7.0
        
        # Heuristiques pour ajuster le score
        if not output or len(output.strip()) < 20:
            score -= 3.0
        if "bien sûr" in output.lower() or "excellente question" in output.lower():
            score -= 1.0
        if "nous allons" in output.lower() or "je vais" in output.lower():
            score -= 0.5
        if task.dimensions.stakes >= 7 and len(output) < 100:
            score -= 2.0
        
        score = max(1.0, min(10.0, score))
        
        # Déterminer la décision
        decision = self._determine_decision(score)
        
        return {
            "scores": {
                "pertinence": round(score, 1),
                "complete": round(score, 1),
                "exactitude": round(score, 1),
                "qualite": round(score, 1),
                "concision": round(score, 1),
            },
            "score_global": round(score, 1),
            "decision": decision,
            "points_forts": ["Contenu livré"],
            "points_faibles": ["Auto-critique indisponible"],
            "ameliorations_concretes": [],
            "alternative_approche": "",
        }
    
    def get_decision_thresholds(self) -> DecisionThresholds:
        """Retourne les seuils de décision actuels."""
        return self.thresholds
    
    def set_decision_thresholds(self, thresholds: DecisionThresholds) -> None:
        """
        Configure les seuils de décision.
        
        Args:
            thresholds: Nouveaux seuils de décision
        """
        self.thresholds = thresholds
