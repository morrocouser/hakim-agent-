"""
HakimAgent - Interface de Base pour les Workers Spécialisés (Étape 3)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from hakim_agent.state import AgentState


class BaseWorker(ABC):
    """
    Classe abstraite pour chaque agent spécialisé (Worker).
    Chaque sous-agent dispose d'outils restreints et précis selon son domaine.
    """

    name: str = "base_worker"
    role: str = "generalist"
    description: str = "Base worker"
    requires_review: bool = False

    @abstractmethod
    async def execute(
        self,
        step: str,
        context: Dict[str, Any],
        state: Optional[AgentState] = None,
    ) -> Dict[str, Any]:
        """
        Exécute la tâche désignée par l'étape.
        Prend le step courant et le dictionnaire de contexte partagé.
        Retourne un dictionnaire contenant les résultats et métadonnées.
        """
        pass

    async def fix(
        self,
        step: str,
        result: Dict[str, Any],
        feedback: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Boucle de correction (style AutoGen / Smolagents auto-fix).
        Appelée si le Reviewer rejette le résultat pour corriger l'erreur
        sur la base du feedback explicite.
        """
        # Comportement par défaut : ré-exécution simple si non surchargé
        return await self.execute(step, context)
