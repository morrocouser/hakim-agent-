"""Définition des offres et forfaits d'abonnement pour HakimAgent."""

from typing import Dict, Any, Optional

PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "id": "free",
        "name": "Starter",
        "badge": "Gratuit",
        "price_monthly_cents": 0,
        "price_yearly_cents": 0,
        "currency": "eur",
        "description": "Pour découvrir l'écosystème multi-agents et prototyper vos prompts en local.",
        "popular": False,
        "features": [
            "Accès aux modèles open-source locaux (Qwen 2.5, Llama 3.1)",
            "10 exécutions de tâches par jour",
            "1 agent actif à la fois (séquentiel)",
            "Mémoire locale SQLite de base",
            "Support communautaire",
        ],
        "limits": {
            "max_daily_runs": 10,
            "parallel_agents": 1,
            "cloud_llm_access": False,
        },
    },
    "pro": {
        "id": "pro",
        "name": "Pro Développeur",
        "badge": "Recommandé",
        "price_monthly_cents": 2900,  # 29.00 EUR (entier minor unit)
        "price_yearly_cents": 27900,  # 279.00 EUR (-20%)
        "currency": "eur",
        "description": "Pour les développeurs et créateurs exigeant la pleine puissance des agents autonomes.",
        "popular": True,
        "features": [
            "Tous les modèles haut de gamme (Claude 3.7 Sonnet, GPT-4o, Gemini 2.0)",
            "Exécutions de tâches illimitées",
            "Orchestration DAG jusqu'à 8 sous-agents en parallèle",
            "Boucle de réflexion ReAct & scoring déterministe complet",
            "Sandbox d'exécution sécurisée des fichiers",
            "Outils Web Search, Code Executor, MCP & Connecteurs",
            "Support prioritaire par email & Discord",
        ],
        "limits": {
            "max_daily_runs": -1,  # illimité
            "parallel_agents": 8,
            "cloud_llm_access": True,
        },
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Entreprise & Équipe",
        "badge": "Échelle",
        "price_monthly_cents": 9900,  # 99.00 EUR
        "price_yearly_cents": 95000,  # 950.00 EUR
        "currency": "eur",
        "description": "Pour les équipes nécessitant des workflows sur-mesure, SLA et haute disponibilité.",
        "popular": False,
        "features": [
            "Toutes les fonctionnalités du forfait Pro",
            "Coworkers & personas d'agents spécialisés illimités",
            "Routage hybride multi-fournisseurs (clés API d'entreprise)",
            "Gouvernance, logs d'audit et politiques de conformité complètes",
            "Déploiement sur cluster dédié / On-Premise",
            "Garantie de disponibilité SLA 99.9%",
            "Ingénieur support dédié & onboarding personnalisé",
        ],
        "limits": {
            "max_daily_runs": -1,
            "parallel_agents": 32,
            "cloud_llm_access": True,
        },
    },
}


def get_plan_by_id(plan_id: str) -> Optional[Dict[str, Any]]:
    """Retourne la configuration d'un plan selon son identifiant."""
    return PLANS.get(plan_id.lower())
