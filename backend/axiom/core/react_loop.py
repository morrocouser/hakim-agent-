from axiom.models.schemas import TaskAssignment, TaskResult, TaskStatus, ModelName, AgentName, TaskType
from axiom.models.memory_models import AxiomMemory
from axiom.core.scoring import score_and_route
from axiom.core.memory import MemoryManager
from axiom.core.prompt_builder import PromptBuilder
from axiom.core.self_critique_engine import SelfCritiqueEngine, DecisionThresholds
from axiom.claude.client import OpenChassisClient, LocalAPIClient
from axiom.core.error_protocol import ErrorProtocol, ErrorContext, ErrorTier, ErrorProtocolResult
from axiom.core.operation_modes import OperationMode, detect_operation_mode, apply_mode_behavior
from axiom.core.user_style import UserStyleDetector, format_response_for_style
from axiom.tools.error_log import ErrorLog
from axiom.tools.web_search import WebSearchTool
from axiom.tools.file_manager import FileManager
from axiom.tools.code_executor import CodeExecutor
from axiom.logging_setup import log
from typing import Optional, Dict, Any, List, Tuple
import os
import time

class ReActLoop:
    """
    Boucle ReAct pour l'exécution de tâches avec auto-critique.
    
    Cette classe coordonne:
    - L'exécution de tâches via LLM
    - La boucle d'itération avec auto-critique
    - La gestion des erreurs via ErrorProtocol
    - L'application du style utilisateur
    
    Args:
        memory: Gestionnaire de mémoire
        claude: Client LLM
        prompt_builder: Constructeur de prompts (optionnel, créé si non fourni)
        self_critique_engine: Moteur d'auto-critique (optionnel, créé si non fourni)
        web_search: Outil de recherche web (optionnel)
        file_manager: Gestionnaire de fichiers (optionnel)
        code_executor: Exécuteur de code (optionnel)
        error_log: Journal d'erreurs (optionnel)
        max_iterations: Nombre maximum d'itérations
    """
    
    def __init__(
        self,
        memory: MemoryManager,
        claude: OpenChassisClient,
        prompt_builder: Optional[PromptBuilder] = None,
        self_critique_engine: Optional[SelfCritiqueEngine] = None,
        web_search: Optional[WebSearchTool] = None,
        file_manager: Optional[FileManager] = None,
        code_executor: Optional[CodeExecutor] = None,
        error_log: Optional[ErrorLog] = None,
        max_iterations: int = 3,
    ):
        self.memory = memory
        self.claude = claude
        self.max_iterations = max_iterations
        
        # Services injectés ou créés
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.self_critique_engine = self_critique_engine or SelfCritiqueEngine(claude)
        self.web_search = web_search or WebSearchTool(os.getenv("WEB_SEARCH_API_KEY", ""))
        self.file_manager = file_manager or FileManager()
        self.code_executor = code_executor or CodeExecutor()
        self.error_log = error_log or ErrorLog(os.getenv("ERROR_LOG_PATH", ""))
        
        # Configuration
        self.tool_loop_enabled = os.getenv("AXIOM_TOOL_LOOP", os.getenv("HAKIM_TOOL_LOOP", "")) == "1"
        
        # État
        self._current_mode: Optional[OperationMode] = None
        self.error_protocol = ErrorProtocol(self.error_log, memory)
        self.user_style_detector = UserStyleDetector(memory)
        self.user_style_detector.load_from_memory()
        
        # Inject user style detector into prompt builder
        self.prompt_builder.user_style_detector = self.user_style_detector

    async def execute(self, task: TaskAssignment, context: Optional[str] = None) -> TaskResult:
        """
        Exécute une tâche avec la boucle ReAct.
        
        La boucle suit ces étapes:
        1. Détection du mode opérationnel
        2. Application des modifications de comportement selon le mode
        3. Recherche web automatique si nécessaire
        4. Exécution itérative avec auto-critique
        5. Retourne le résultat final
        
        Args:
            task: Assignment de tâche avec agent, modèle et score
            context: Contexte supplémentaire pour la tâche
            
        Returns:
            TaskResult avec statut, output, erreur et score de qualité
        """
        log.info("🔄 REACT LOOP DÉMARRÉ")
        log.info("   Tâche: %s", task.description[:80])
        log.info("   Agent: %s | Score: %s/10", task.agent.value, task.score)

        # Detect operation mode
        self._current_mode = detect_operation_mode(
            task.description,
            self._infer_task_type(task.agent),
            task.dimensions,
            context
        )
        log.info("   Mode détecté: %s", self._current_mode.value)

        # Apply mode behavior modifications
        mode_config = apply_mode_behavior(self._current_mode, task, {"context": context})
        effective_max_iterations = mode_config.get("max_iterations", self.max_iterations)
        log.info("   Max itérations: %s", effective_max_iterations)

        # RECHERCHE mode or RESEARCHER agent: execute web search automatically
        if self._current_mode == OperationMode.RECHERCHE or task.agent == AgentName.RESEARCHER:
            search_query = task.description
            log.info("   🌐 RECHERCHE WEB automatique: %s", search_query[:60])
            search_results = await self.web_search.search(search_query)
            log.info("   🌐 Résultats reçus: %s caractères", len(str(search_results)))
            context = f"{context}\n\n[RÉSULTATS RECHERCHE WEB]:\n{search_results}" if context else f"[RÉSULTATS RECHERCHE WEB]:\n{search_results}"

        # Override model if specified (e.g., URGENCE mode)
        if "model_override" in mode_config:
            task.model = mode_config["model_override"]

        # Adjust speed_need for URGENCE mode
        if "speed_adjustment" in mode_config:
            task.dimensions.speed_need = max(1, min(10, task.dimensions.speed_need + mode_config["speed_adjustment"]))

        self.memory.set_current_task(
            task_id=task.task_id,
            description=task.description,
            task_type=task.agent.value,
            agent=task.agent.value,
            model=task.model.value,
            score=task.score,
        )

        iteration = 1
        quality = 0.0
        last_output = None
        last_error = None
        self_critique_results = []

        while iteration <= effective_max_iterations:
            log.info("   ─── Itération %s/%s ───", iteration, effective_max_iterations)
            t_iter = time.time()
            output, error = await self._execute_iteration(task, context, iteration, effective_max_iterations)
            elapsed = round(time.time() - t_iter, 2)

            if error:
                log.warning("   ⚠️  ERREUR itération %s (%ss): %s", iteration, elapsed, str(error)[:120])
                error_obj = Exception(error) if isinstance(error, str) else error
                protocol_result = await self.error_protocol.handle_error(
                    error=error_obj,
                    task=task,
                    context=context or task.description,
                    iteration=iteration,
                )

                if protocol_result.should_continue:
                    if protocol_result.fallback_result:
                        context = str(protocol_result.fallback_result)
                        iteration += 1
                        continue
                    elif protocol_result.requires_user_input:
                        last_error = protocol_result.user_message
                        quality = 4.0
                        break
                    else:
                        iteration += 1
                        continue
                else:
                    last_error = protocol_result.user_message
                    quality = 4.0
                    break

            # SELF-CRITIQUE: Evaluate output quality
            if output:
                # Sur les tâches simples (score < 6), évaluation heuristique rapide pour éviter de doubler la latence/coût
                should_full_critique = (
                    task.score >= 6.0
                    or self._current_mode == OperationMode.ITERATIF
                    or os.getenv("AXIOM_SELF_CRITIQUE_ALL", "") == "1"
                )

                if should_full_critique:
                    log.info("   🧠 AUTO-CRITIQUE LLM en cours (%s caractères)...", len(output))
                    critique = await self._self_critique(
                        task=task,
                        output=output,
                        iteration=iteration,
                        max_iterations=effective_max_iterations,
                    )
                else:
                    log.info("   ⚡ ÉVALUATION RAPIDE (tâche simple score=%s)...", task.score)
                    critique = self.self_critique_engine._fallback_quality_eval(output, task)


                self_critique_results.append(critique)
                quality = critique["score_global"]
                last_output = output

                # Check if we should continue iterating based on self-critique
                decision = critique["decision"]
                log.info("   📊 Auto-critique: score=%s/10 | décision=%s", quality, decision)

                if decision == "LIVRAISON":
                    log.info("   ✅ LIVRAISON acceptée — sortie validée")
                    break
                elif decision == "ITERATION" and iteration < effective_max_iterations:
                    log.info("   🔄 ITERATION demandée — ré-essaie avec auto-critique")
                    context = f"Auto-critique: {critique['points_faibles']}. Améliorations: {critique['ameliorations_concretes']}"
                    iteration += 1
                    continue
                elif decision == "REPLAN" and iteration < effective_max_iterations:
                    log.info("   🔁 REPLAN complet demandé")
                    context = f"Replanification complète requise. {critique['alternative_approche']}"
                    iteration += 1
                    continue
                elif decision == "PARTIEL" or iteration >= effective_max_iterations:
                    log.info("   ⚠️  PARTIEL ou max itérations atteint")
                    break
                else:
                    # LIVRAISON with note or continue
                    if iteration < effective_max_iterations:
                        iteration += 1
                        continue
                    break
            else:
                # Une sortie vide est acceptable comme fin de boucle si le LLM n'a rien produit.
                # On ne relance pas une nouvelle tentative automatiquement dans ce cas, sinon on
                # boucle indéfiniment sur des réponses vides et on casse le flux de test / runtime.
                log.warning("   ⚠️  Sortie vide reçue à l'itération %s/%s — clôture de la boucle sans erreur", iteration, effective_max_iterations)
                last_output = output or ""
                quality = 0.0
                break

        # Determine final status
        if quality >= 6.0 and not last_error:
            status = TaskStatus.DONE
            log.info("   ✅ TÂCHE TERMINÉE — score qualité %s/10", quality)
        else:
            status = TaskStatus.FAILED
            log.info("   ❌ TÂCHE ÉCHOUÉE — score qualité %s/10", quality)
        if last_error:
            status = TaskStatus.FAILED
            log.error("   ❌ Erreur finale: %s", last_error[:120])

        self.memory.update_task_status(status.value, quality)
        self.memory.add_to_history(
            task_id=task.task_id,
            resume=task.description,
            task_type=task.agent.value,
            model=task.model.value,
            outcome="SUCCESS" if status == TaskStatus.DONE else "FAILED",
        )

        # Build final output with self-critique summary if verbose
        final_output = last_output
        if self_critique_results and self_critique_results[-1]["decision"] != "LIVRAISON":
            final_critique = self_critique_results[-1]
            final_output = f"{last_output}\n\n---\n🔍 AUTO-CRITIQUE (itération {len(self_critique_results)}):\n" \
                          f"Score global: {final_critique['score_global']}/10\n" \
                          f"Décision: {final_critique['decision']}\n" \
                          f"Points forts: {', '.join(final_critique['points_forts'])}\n" \
                          f"Points faibles: {', '.join(final_critique['points_faibles'])}"

        # Apply user style formatting to final output
        if final_output:
            final_output = format_response_for_style(
                final_output,
                self.user_style_detector.get_current_style(),
                task.agent.value,
                task.model.value,
            )

        # Save detected style to memory
        self.user_style_detector.save_to_memory()

        return TaskResult(
            task_id=task.task_id,
            description=task.description,
            agent=task.agent,
            model=task.model,
            score=task.score,
            status=status,
            output=final_output,
            error=last_error,
            iteration=iteration,
            quality_score=round(quality, 1),
        )

    async def _execute_iteration(
        self,
        task: TaskAssignment,
        context: Optional[str],
        iteration: int,
        max_iterations: int,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Exécute une itération de la boucle ReAct.
        
        Args:
            task: Assignment de tâche
            context: Contexte supplémentaire
            iteration: Numéro de l'itération (1-based)
            max_iterations: Nombre maximum d'itérations
            
        Returns:
            Tuple de (output, error) où output est la réponse du LLM
            et error est None si succès
        """
        # Utiliser le PromptBuilder pour construire les prompts
        system_prompt = self.prompt_builder.build_system_prompt(
            task=task,
            iteration=iteration,
            max_iterations=max_iterations,
            current_mode=self._current_mode,
        )
        user_prompt = self.prompt_builder.build_user_prompt(
            task=task,
            context=context,
            iteration=iteration,
            max_iterations=max_iterations,
            current_mode=self._current_mode,
        )

        try:
            if self.tool_loop_enabled:
                log.info("   🔧 TOOL LOOP v2 activée (HAKIM_TOOL_LOOP=1)")
                from axiom.core.tool_loop_v2 import run_tool_loop_v2
                ctx = {
                    "web_search": self.web_search,
                    "file_manager": self.file_manager,
                    "code_executor": self.code_executor,
                    "error_log": self.error_log,
                }
                t_llm = time.time()
                result = await run_tool_loop_v2(
                    self.claude, task.model.value, system_prompt, user_prompt, ctx,
                )
                log.info("   📡 Tool Loop terminé en %ss (%s caractères)", round(time.time() - t_llm, 2), len(result) if result else 0)
                return result, None
            log.info("   📡 Appel LLM: %s...", task.model.value)
            t_llm = time.time()
            response = await self.claude.chat(
                model=task.model.value,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            elapsed = round(time.time() - t_llm, 2)
            log.info("   📡 LLM réponse reçue en %ss (%s caractères)", elapsed, len(response) if response else 0)
            return response, None
        except Exception as e:
            log.error("   ❌ Exception itération %s: %s", iteration, str(e)[:120])
            return None, str(e)

    async def _self_critique(
        self,
        task: TaskAssignment,
        output: str,
        iteration: int,
        max_iterations: int,
    ) -> dict:
        """
        Exécute l'auto-critique en utilisant le SelfCritiqueEngine.
        
        Args:
            task: Assignment de tâche
            output: Sortie générée par le LLM
            iteration: Itération actuelle
            max_iterations: Nombre maximum d'itérations
            
        Returns:
            Dictionnaire avec scores, décision, points forts/faibles, etc.
        """
        # Déléguer au SelfCritiqueEngine
        return await self.self_critique_engine.evaluate(
            task=task,
            output=output,
            iteration=iteration,
            max_iterations=max_iterations,
        )

    def _infer_task_type(self, agent: AgentName) -> TaskType:
        """Map agent to task type for mode detection."""
        mapping = {
            AgentName.ARCHITECT: TaskType.ARCH,
            AgentName.CODER: TaskType.CODE,
            AgentName.DEBUGGER: TaskType.DEBUG,
            AgentName.ANALYST: TaskType.DATA,
            AgentName.WRITER: TaskType.DOC,
            AgentName.RESEARCHER: TaskType.RESEARCH,
            AgentName.PLANNER: TaskType.PLAN,
            AgentName.QUICKSHOT: TaskType.QUICK,
        }
        return mapping.get(agent, TaskType.QUICK)