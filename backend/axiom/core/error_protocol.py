"""
AXIOM v4.0 — Protocole d'Erreur 5 Tiers
TIER_0: PRÉVENTION (avant exécution)
TIER_1: AUTO-CORRECTION (sans interruption)
TIER_2: CLARIFICATION (1 question structurée)
TIER_3: DÉGRADATION GRACIEUSE
TIER_4: REFUS JUSTIFIÉ
TIER_5: ESCALADE UTILISATEUR
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from axiom.models.schemas import TaskAssignment
from axiom.tools.error_log import ErrorLog
from axiom.core.memory import MemoryManager


class ErrorTier(int, Enum):
    PREVENTION = 0
    AUTO_CORRECTION = 1
    CLARIFICATION = 2
    GRACEFUL_DEGRADATION = 3
    JUSTIFIED_REFUSAL = 4
    USER_ESCALATION = 5


@dataclass
class ErrorContext:
    tier: ErrorTier
    agent: str
    context: str
    symptom: str
    root_cause: str = ""
    fix: str = ""
    lesson: str = ""
    score: int = 5
    original_error: Optional[Exception] = None
    recoverable: bool = True
    user_message: str = ""
    alternatives: List[str] = field(default_factory=list)


@dataclass
class ErrorProtocolResult:
    tier: ErrorTier
    handled: bool
    action_taken: str
    user_message: Optional[str] = None
    requires_user_input: bool = False
    fallback_result: Optional[Any] = None
    should_continue: bool = True
    modified_task: Optional[TaskAssignment] = None


class ErrorProtocol:
    """
    Protocole de gestion d'erreurs 5 tiers pour AXIOM.
    S'intègre dans la boucle ReAct pour gestion transparente.
    """

    def __init__(
        self,
        error_log: ErrorLog,
        memory: MemoryManager,
        max_auto_correction_attempts: int = 2,
    ):
        self.error_log = error_log
        self.memory = memory
        self.max_auto_correction_attempts = max_auto_correction_attempts
        self._auto_correction_count: Dict[str, int] = {}
        self._clarification_pending: Optional[ErrorContext] = None

        # Handlers par tier
        self.tier_handlers: Dict[ErrorTier, Callable] = {
            ErrorTier.PREVENTION: self._handle_prevention,
            ErrorTier.AUTO_CORRECTION: self._handle_auto_correction,
            ErrorTier.CLARIFICATION: self._handle_clarification,
            ErrorTier.GRACEFUL_DEGRADATION: self._handle_graceful_degradation,
            ErrorTier.JUSTIFIED_REFUSAL: self._handle_justified_refusal,
            ErrorTier.USER_ESCALATION: self._handle_user_escalation,
        }

    async def handle_error(
        self,
        error: Exception,
        task: TaskAssignment,
        context: str = "",
        iteration: int = 1,
    ) -> ErrorProtocolResult:
        """
        Point d'entrée principal: détermine le tier et traite l'erreur.
        """
        # Analyser l'erreur pour déterminer le tier approprié
        tier = self._classify_error(error, task, context, iteration)

        error_ctx = ErrorContext(
            tier=tier,
            agent=task.agent.value,
            context=context or task.description,
            symptom=str(error),
            original_error=error,
        )

        # Exécuter le handler approprié
        handler = self.tier_handlers[tier]
        return await handler(error_ctx, task, iteration)

    def _classify_error(
        self,
        error: Exception,
        task: TaskAssignment,
        context: str,
        iteration: int,
    ) -> ErrorTier:
        """Classifie une erreur dans un des 5 tiers."""

        error_msg = str(error).lower()
        error_type = type(error).__name__

        # TIER_5: Escalade - décisions stratégiques, ambiguïté totale
        escalation_keywords = [
            "stratégique", "irréversible", "architectural", "choix technologique",
            "budget", "équipe", "licence", "légal", "conformité", "sécurité critique"
        ]
        if any(kw in context.lower() for kw in escalation_keywords):
            return ErrorTier.USER_ESCALATION

        # TIER_4: Refus - sécurité, éthique, destruction données
        refusal_keywords = [
            "injection", "xss", "csrf", "sql injection", "rce", "exploit",
            "mot de passe", "secret", "clé privée", "token", "credential",
            "supprimer", "delete", "drop table", "truncate", "format",
            "effacer", "destroy", "wipe", "malveillant", "attaque"
        ]
        if any(kw in error_msg for kw in refusal_keywords):
            return ErrorTier.JUSTIFIED_REFUSAL

        # TIER_3: Dégradation - modèle indisponible, outil en erreur, résultat partiel
        degradation_keywords = [
            "rate limit", "quota", "unavailable", "indisponible", "timeout",
            "connection refused", "connexion refusée", "service unavailable",
            "503", "502", "504", "overloaded", "surchargé"
        ]
        if any(kw in error_msg for kw in degradation_keywords):
            return ErrorTier.GRACEFUL_DEGRADATION

        # TIER_2: Clarification - intention ambiguë, données manquantes
        clarification_keywords = [
            "ambigu", "plusieurs interprétations", "manquant", "missing",
            "quelle", "quoi", "comment", "précise", "spécifie", "détail"
        ]
        # Si c'est la première itération et qu'on a pas assez de contexte
        if iteration == 1 and (
            any(kw in context.lower() for kw in clarification_keywords)
            or len(context.strip()) < 50
        ):
            return ErrorTier.CLARIFICATION

        # TIER_1: Auto-correction - syntaxe, import, type, format, logique évidente
        auto_correction_keywords = [
            "syntax", "syntaxe", "import", "module", "not found", "introuvable",
            "type", "mismatch", "incompatible", "expected", "attendu",
            "indentation", "indent", "bracket", "parenthèse", "accolade",
            "undefined", "non défini", "reference", "référence", "nameerror",
            "attributeerror", "keyerror", "indexerror", "valueerror"
        ]
        if any(kw in error_msg for kw in auto_correction_keywords):
            # Vérifier si on a déjà tenté l'auto-correction
            error_key = f"{task.task_id}:{error_type}:{error_msg[:50]}"
            if self._auto_correction_count.get(error_key, 0) < self.max_auto_correction_attempts:
                return ErrorTier.AUTO_CORRECTION
            # Sinon, passer au tier supérieur
            return ErrorTier.CLARIFICATION

        # TIER_0: Prévention - consulté AVANT exécution
        # (géré en amont, pas ici)

        # Par défaut: clarification
        return ErrorTier.CLARIFICATION

    async def _handle_prevention(
        self,
        error_ctx: ErrorContext,
        task: TaskAssignment,
        iteration: int,
    ) -> ErrorProtocolResult:
        """TIER_0: Consultation ERROR_LOG avant exécution pour éviter erreurs connues."""
        lessons = self.error_log.get_lessons(context=error_ctx.context, min_score=5)

        if lessons:
            # Appliquer les leçons apprises
            applied_lessons = []
            for lesson in lessons[:3]:  # Max 3 leçons
                applied_lessons.append(lesson.lesson)

            return ErrorProtocolResult(
                tier=ErrorTier.PREVENTION,
                handled=True,
                action_taken=f"Leçons appliquées: {'; '.join(applied_lessons)}",
                user_message=f"⚠️ Prévention: {len(lessons)} leçon(s) du ERROR_LOG appliquée(s)",
                should_continue=True,
            )

        return ErrorProtocolResult(
            tier=ErrorTier.PREVENTION,
            handled=False,
            action_taken="Aucune leçon applicable trouvée",
            should_continue=True,
        )

    async def _handle_auto_correction(
        self,
        error_ctx: ErrorContext,
        task: TaskAssignment,
        iteration: int,
    ) -> ErrorProtocolResult:
        """TIER_1: Auto-correction sans interruption utilisateur."""
        error_key = f"{task.task_id}:{type(error_ctx.original_error).__name__}:{error_ctx.symptom[:50]}"
        self._auto_correction_count[error_key] = self._auto_correction_count.get(error_key, 0) + 1

        # Construire le prompt de correction
        correction_prompt = self._build_correction_prompt(error_ctx, task)

        # Logger l'erreur pour apprentissage futur
        self.error_log.log(
            tier=1,
            agent=error_ctx.agent,
            context=error_ctx.context,
            symptom=error_ctx.symptom,
            root_cause=error_ctx.root_cause or "À déterminer par auto-correction",
            fix="Auto-correction en cours...",
            lesson="En attente de résolution",
            score=5,
        )

        return ErrorProtocolResult(
            tier=ErrorTier.AUTO_CORRECTION,
            handled=True,
            action_taken=f"Tentative auto-correction #{self._auto_correction_count[error_key]}",
            user_message=f"⚠️ Auto-corrigé: {error_ctx.symptom[:100]}",
            should_continue=True,
            fallback_result=correction_prompt,  # Sera utilisé par ReActLoop pour retry
        )

    def _build_correction_prompt(self, error_ctx: ErrorContext, task: TaskAssignment) -> str:
        return (
            f"ERREUR À CORRIGER (tentative auto-correction):\n"
            f"Agent: {error_ctx.agent}\n"
            f"Tâche: {task.description}\n"
            f"Erreur: {error_ctx.symptom}\n"
            f"Contexte: {error_ctx.context}\n\n"
            f"Applique un fix MINIMAL uniquement. Ne refactorise pas.\n"
            f"Retourne le code/output corrigé complet."
        )

    async def _handle_clarification(
        self,
        error_ctx: ErrorContext,
        task: TaskAssignment,
        iteration: int,
    ) -> ErrorProtocolResult:
        """TIER_2: Clarification avec 1 question structurée forcée."""
        # Générer une question précise basée sur l'erreur/contexte
        question = self._generate_clarification_question(error_ctx, task)

        # Stocker pour attendre la réponse
        self._clarification_pending = error_ctx

        return ErrorProtocolResult(
            tier=ErrorTier.CLARIFICATION,
            handled=True,
            action_taken="Clarification demandée à l'utilisateur",
            user_message=question,
            requires_user_input=True,
            should_continue=False,  # Attendre réponse
        )

    def _generate_clarification_question(self, error_ctx: ErrorContext, task: TaskAssignment) -> str:
        """Génère une question de clarification structurée (format imposé)."""
        base = f"❓ Clarification requise pour: {task.description[:100]}\n\n"

        # Analyser ce qui manque
        if "ambigu" in error_ctx.symptom.lower() or len(error_ctx.context) < 50:
            return base + (
                "L'intention n'est pas claire. Choisis une option:\n"
                "A) [Option A — conséquence]\n"
                "B) [Option B — conséquence]\n"
                "C) [Option C — conséquence]"
            )

        if "manquant" in error_ctx.symptom.lower() or "missing" in error_ctx.symptom.lower():
            return base + (
                "Données critiques manquantes. Choisis:\n"
                "A) Fournir les données maintenant\n"
                "B) Utiliser valeurs par défaut (risque: résultat générique)\n"
                "C) Annuler la tâche"
            )

        # Question générique structurée
        return base + (
            "Deux interprétations valides détectées. Choisis:\n"
            "A) [Interprétation A — conséquence]\n"
            "B) [Interprétation B — conséquence]\n"
            "C) [Autre — précise]"
        )

    def provide_clarification_answer(self, answer: str) -> Optional[ErrorContext]:
        """Appelé quand l'utilisateur répond à une clarification."""
        if self._clarification_pending:
            ctx = self._clarification_pending
            self._clarification_pending = None
            return ctx
        return None

    async def _handle_graceful_degradation(
        self,
        error_ctx: ErrorContext,
        task: TaskAssignment,
        iteration: int,
    ) -> ErrorProtocolResult:
        """TIER_3: Dégradation gracieuse - livre ce qui est possible."""
        # Logger
        self.error_log.log(
            tier=3,
            agent=error_ctx.agent,
            context=error_ctx.context,
            symptom=error_ctx.symptom,
            root_cause="Service/model indisponible ou partiel",
            fix="Dégradation gracieuse appliquée",
            lesson="Prévoir fallback pour ce service",
            score=6,
        )

        # Construire message de livraison partielle
        partial_msg = (
            f"⚡ Livraison partielle: Tâche '{task.description[:80]}' "
            f"exécutée avec limitations\n"
            f"⚠️ Manquant: {error_ctx.symptom}\n"
            f"🔄 Alternative: Réessaie plus tard ou utilise modèle local"
        )

        return ErrorProtocolResult(
            tier=ErrorTier.GRACEFUL_DEGRADATION,
            handled=True,
            action_taken="Dégradation gracieuse - résultat partiel livré",
            user_message=partial_msg,
            should_continue=True,
            fallback_result={
                "partial": True,
                "reason": error_ctx.symptom,
                "suggestion": "Réessaie plus tard ou change de modèle",
            },
        )

    async def _handle_justified_refusal(
        self,
        error_ctx: ErrorContext,
        task: TaskAssignment,
        iteration: int,
    ) -> ErrorProtocolResult:
        """TIER_4: Refus justifié - sécurité, éthique, risque destruction."""
        # Logger comme CRITICAL
        self.error_log.log(
            tier=4,
            agent=error_ctx.agent,
            context=error_ctx.context,
            symptom=error_ctx.symptom,
            root_cause="Violation contrainte sécurité/éthique",
            fix="Tâche refusée",
            lesson="Ne pas tenter cette opération",
            score=10,
        )

        refusal_msg = (
            f"❌ Refus justifié: Cette tâche ne peut pas être exécutée.\n\n"
            f"Raison: {error_ctx.symptom}\n\n"
            f"Alternative safe: Reformule ta demande sans opération risquée, "
            f"ou contacte l'administrateur si c'est légitime."
        )

        return ErrorProtocolResult(
            tier=ErrorTier.JUSTIFIED_REFUSAL,
            handled=True,
            action_taken="Tâche refusée pour raison de sécurité/éthique",
            user_message=refusal_msg,
            should_continue=False,
        )

    async def _handle_user_escalation(
        self,
        error_ctx: ErrorContext,
        task: TaskAssignment,
        iteration: int,
    ) -> ErrorProtocolResult:
        """TIER_5: Escalade utilisateur - décision stratégique irréversible."""
        # Logger
        self.error_log.log(
            tier=5,
            agent=error_ctx.agent,
            context=error_ctx.context,
            symptom=error_ctx.symptom,
            root_cause="Décision stratégique requise",
            fix="En attente décision utilisateur",
            lesson="Documenter la décision prise",
            score=9,
        )

        escalation_msg = (
            f"⬆️ ESCALADE: Décision stratégique requise.\n\n"
            f"Problème: {error_ctx.symptom}\n"
            f"Contexte: {error_ctx.context}\n\n"
            f"Options:\n"
            f"  A) [Option A — trade-offs complets]\n"
            f"  B) [Option B — trade-offs complets]\n"
            f"  C) [Option C — trade-offs complets]\n\n"
            f"Réponds avec A, B ou C pour continuer."
        )

        return ErrorProtocolResult(
            tier=ErrorTier.USER_ESCALATION,
            handled=True,
            action_taken="Escalade vers utilisateur pour décision stratégique",
            user_message=escalation_msg,
            requires_user_input=True,
            should_continue=False,
        )

    def reset_auto_correction_counter(self, task_id: str):
        """Remet à zéro les compteurs d'auto-correction pour une tâche."""
        keys_to_remove = [k for k in self._auto_correction_count if k.startswith(task_id)]
        for k in keys_to_remove:
            del self._auto_correction_count[k]

    def get_error_stats(self) -> Dict[str, Any]:
        """Statistiques du protocole d'erreur."""
        all_errors = self.error_log.get_all()
        tier_counts = {tier.name: 0 for tier in ErrorTier}
        for e in all_errors:
            tier_name = ErrorTier(e.tier).name if e.tier < len(ErrorTier) else "UNKNOWN"
            tier_counts[tier_name] = tier_counts.get(tier_name, 0) + 1

        return {
            "total_errors_logged": len(all_errors),
            "by_tier": tier_counts,
            "auto_correction_attempts": sum(self._auto_correction_count.values()),
            "clarification_pending": self._clarification_pending is not None,
        }