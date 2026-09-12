from PySide6.QtCore import QThread, Signal
from axiom.claude.client import OpenRouterClient
from axiom.core.scoring import score_and_route
from axiom.core.memory import MemoryManager


class ChatWorker(QThread):
    finished = Signal(str, str, float, float, str)
    error = Signal(str)

    def __init__(self, message: str, api_key: str = "",
                 agent: str = "", model: str = "",
                 memory: MemoryManager = None, parent=None):
        super().__init__(parent)
        self.message = message
        self.api_key = api_key
        self.forced_agent = agent
        self.forced_model = model
        self.memory = memory
        self._cancelled = False

    def run(self):
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._execute())
            finally:
                loop.close()
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))

    async def _execute(self):
        assignment = score_and_route(self.message)
        if self.forced_agent:
            assignment.agent = self.forced_agent
        if self.forced_model:
            assignment.model = self.forced_model
        if self._cancelled:
            return

        client = OpenRouterClient(api_key=self.api_key)
        system_prompt = (
            f"Tu es {assignment.agent.value}. "
            f"Score: {assignment.score}/10. "
            f"Modèle: {assignment.model.value}. "
            f"Zéro filler. Pas de \"Bien sûr!\" ni \"Excellente question!\". "
            f"Réponds directement et densément."
        )
        if self._cancelled:
            return

        response = await client.chat(
            model=assignment.model.value,
            system=system_prompt,
            messages=[{"role": "user", "content": self.message}],
        )
        if self._cancelled:
            return

        agent_str = assignment.agent.value
        model_str = assignment.model.value
        score_val = assignment.score

        if self.memory:
            self.memory.add_to_history(
                task_id=assignment.task_id,
                resume=self.message[:30],
                task_type=agent_str,
                model=model_str,
                outcome="SUCCESS",
            )
            self.memory.compress_if_needed()

        self.finished.emit(
            response,
            agent_str,
            score_val,
            8.0,
            "DONE",
        )

    def cancel(self):
        self._cancelled = True
