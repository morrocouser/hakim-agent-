import httpx
import json
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str
    content: str
    agent: Optional[str] = None
    model: Optional[str] = None
    score: Optional[float] = None
    quality: Optional[float] = None
    status: str = "DONE"
    error: Optional[str] = None


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=180.0)
        self._streaming_supported = None

    async def close(self):
        await self.client.aclose()

    async def health(self) -> Dict[str, Any]:
        resp = await self.client.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()

    async def get_agents(self) -> Dict[str, Any]:
        resp = await self.client.get(f"{self.base_url}/agents")
        resp.raise_for_status()
        return resp.json()

    async def get_memory(self) -> Dict[str, Any]:
        resp = await self.client.get(f"{self.base_url}/memory")
        resp.raise_for_status()
        return resp.json()

    async def score_task(self, description: str, task_type: str = "QUICK") -> Dict[str, Any]:
        resp = await self.client.post(
            f"{self.base_url}/score",
            json={"description": description, "task_type": task_type}
        )
        resp.raise_for_status()
        return resp.json()

    async def execute_task(self, description: str, task_type: str = "QUICK", context: Optional[str] = None) -> Dict[str, Any]:
        resp = await self.client.post(
            f"{self.base_url}/execute",
            json={"description": description, "task_type": task_type, "context": context}
        )
        resp.raise_for_status()
        return resp.json()

    async def chat(self, message: str, agent: Optional[str] = None, model: Optional[str] = None) -> ChatMessage:
        payload = {"role": "user", "content": message}
        if agent:
            payload["agent"] = agent
        if model:
            payload["model"] = model

        resp = await self.client.post(f"{self.base_url}/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        task = data.get("task", {})
        return ChatMessage(
            role="assistant",
            content=data.get("response", ""),
            agent=task.get("agent"),
            model=task.get("model"),
            score=task.get("score"),
            quality=task.get("quality_score"),
            status=task.get("status", "DONE"),
            error=task.get("error"),
        )

    async def chat_stream(
        self,
        message: str,
        agent: Optional[str] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response token by token. Falls back to non-streaming if not supported."""
        payload = {"role": "user", "content": message}
        if agent:
            payload["agent"] = agent
        if model:
            payload["model"] = model

        # Try streaming endpoint first
        if self._streaming_supported is not False:
            try:
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/chat/stream",
                    json=payload,
                    timeout=180.0
                ) as resp:
                    if resp.status_code == 200:
                        self._streaming_supported = True
                        async for chunk in resp.aiter_text():
                            if chunk:
                                yield chunk
                        return
                    elif resp.status_code == 404:
                        self._streaming_supported = False
            except Exception:
                self._streaming_supported = False

        # Fallback: simulate streaming by chunking the full response
        result = await self.chat(message, agent, model)
        content = result.content
        # Yield in chunks of ~20 chars for visual effect
        chunk_size = 20
        for i in range(0, len(content), chunk_size):
            yield content[i:i+chunk_size]
            await asyncio.sleep(0.01)

    async def set_project(self, name: str, project_type: str = "SaaS", description: str = "", client: str = "Interne"):
        resp = await self.client.post(f"{self.base_url}/memory/project", json={
            "name": name, "project_type": project_type, "description": description, "client": client
        })
        resp.raise_for_status()

    async def set_stack(self, **kwargs):
        resp = await self.client.post(f"{self.base_url}/memory/stack", json=kwargs)
        resp.raise_for_status()

    async def add_decision(self, decision: str, reason: str, revocable: bool = False):
        resp = await self.client.post(f"{self.base_url}/memory/decision", json={
            "decision": decision, "reason": reason, "revocable": revocable
        })
        resp.raise_for_status()