import os
import time
import asyncio
import httpx
import json
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from axiom.logging_setup import log

# Load .env relative to backend directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# API endpoints
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENCODE_CONSOLE_BASE = "https://console.opencode.ai/inference/openai/v1"
LOCAL_API_BASE = os.getenv("OPENCHASSIS_API_BASE")
APP_REFERRER = "https://github.com/hakimagent/axiom"
APP_TITLE = "APEX v4.0 Orchestrateur"

DEFAULT_RPM = 20
DEFAULT_TPM = 100000


class TokenBucketRateLimiter:
    def __init__(self, rpm: int = DEFAULT_RPM, tpm: int = DEFAULT_TPM):
        self.rpm = rpm
        self.tpm = tpm
        self.request_tokens = rpm
        self.token_tokens = tpm
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 1000) -> None:
        effective_tokens = min(estimated_tokens, self.tpm)
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            if elapsed >= 1.0:
                self.request_tokens = self.rpm
                self.token_tokens = self.tpm
                self.last_refill = now

            while self.request_tokens <= 0 or self.token_tokens < effective_tokens:
                wait_time = max(0.05, 1.0 - (now - self.last_refill))
                await asyncio.sleep(wait_time)
                now = time.monotonic()
                elapsed = now - self.last_refill
                if elapsed >= 1.0:
                    self.request_tokens = self.rpm
                    self.token_tokens = self.tpm
                    self.last_refill = now

            self.request_tokens -= 1
            self.token_tokens -= effective_tokens



class LocalAPIClient:
    """Client API unifié : base résolue via HAKIM_LLM_BASE_URL,
    sinon OPENCHASSIS_API_BASE (repli local), sinon la passerelle
    Console opencode ; clé via HAKIM_LLM_API_KEY (repli
    OPENROUTER_API_KEY si la base est OpenRouter)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        rpm: int = DEFAULT_RPM,
        tpm: int = DEFAULT_TPM,
    ):
        self.api_key = api_key or ""
        self.base_url = (
            os.getenv("HAKIM_LLM_BASE_URL")
            or LOCAL_API_BASE
            or OPENCODE_CONSOLE_BASE
        )
        self._api_key = os.getenv("HAKIM_LLM_API_KEY") or self.api_key
        if not self._api_key and "openrouter.ai" in self.base_url:
            self._api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.api_key = self._api_key
        self.http = httpx.AsyncClient(timeout=120)
        self.rate_limiter = TokenBucketRateLimiter(rpm=rpm, tpm=tpm)

    async def chat(self, model: str, system: str,
                   messages: list[dict], max_tokens: int = 4096) -> str:
        model = os.getenv("HAKIM_LLM_MODEL") or model
        estimated_tokens = max_tokens + len(system) // 4 + sum(len(m.get("content", "")) for m in messages) // 4
        await self.rate_limiter.acquire(estimated_tokens)

        log.info("   📡 LLM → %s (est. %s tokens)", model, estimated_tokens)

        body = {
            "model": model,
            "messages": [{"role": "system", "content": system}] + messages,
            "max_tokens": max_tokens,
        }

        # Headers : inclure Authorization + HTTP-Referer pour OpenRouter
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": APP_REFERRER,
            "X-Title": APP_TITLE,
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            t0 = time.time()
            resp = await self.http.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=body,
            )
            elapsed = round(time.time() - t0, 2)
            text = resp.text

            # Essayer de parser directement d'abord (plus robuste)
            data = None
            parse_error = None
            
            # Tentative 1: Parser directement
            try:
                data = json.loads(text)
            except json.JSONDecodeError as e:
                parse_error = e
                log.debug("Échec parsing JSON direct: %s", str(e))
            
            # Tentative 2: Nettoyer la réponse si c'est du streaming SSE
            if data is None and ("data: " in text or "data: [DONE]" in text):
                # Extraire tous les chunks JSON de la réponse SSE
                json_chunks = []
                for line in text.split("\n"):
                    line = line.strip()
                    if line.startswith("data: ") and not line.endswith("[DONE]"):
                        chunk_data = line[6:].strip()  # Enlever "data: "
                        if chunk_data:
                            try:
                                chunk = json.loads(chunk_data)
                                if isinstance(chunk, dict):
                                    json_chunks.append(chunk)
                            except json.JSONDecodeError:
                                continue
                
                # Reconstruire la réponse complète
                if json_chunks:
                    # Pour le chat normal, on prend le dernier chunk
                    data = json_chunks[-1]
                    # Si c'est un completions endpoint, on merge les chunks
                    if "choices" in json_chunks[0]:
                        # Fusionner les choix
                        merged_choices = []
                        for chunk in json_chunks:
                            if "choices" in chunk:
                                for i, choice in enumerate(chunk["choices"]):
                                    if i < len(merged_choices):
                                        # Accumuler le contenu
                                        if "delta" in choice:
                                            merged_choices[i]["message"]["content"] = \
                                                merged_choices[i].get("message", {}).get("content", "") + \
                                                choice["delta"].get("content", "")
                                        elif "message" in choice:
                                            merged_choices[i] = choice
                                    else:
                                        merged_choices.append(choice)
                        data = {"choices": merged_choices}
                        if "usage" in json_chunks[-1]:
                            data["usage"] = json_chunks[-1]["usage"]
            
            # Tentative 3: Extraction manuelle (dernier recours)
            if data is None and parse_error:
                log.warning("Tentative de nettoyage manuel du JSON")
                # Supprimer le SSE wrapper
                if "data: [DONE]" in text:
                    text = text.split("data: [DONE]")[0].strip()
                # Trouver le JSON principal
                start_idx = text.find("{")
                end_idx = text.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    text = text[start_idx:end_idx+1]
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError as e:
                        log.error("Échec parsing JSON après nettoyage: %s", str(e))
                        raise ValueError(f"Réponse non-JSON valide: {text[:200]}")
            
            if data is None:
                raise ValueError(f"Impossible de parser la réponse JSON: {text[:200]}")

            if resp.is_error:
                err = data.get("error", "")
                if isinstance(err, dict):
                    error_msg = err.get("message", str(resp.status_code))
                else:
                    error_msg = str(err) if err else str(resp.status_code)
                log.error("   ❌ LLM erreur HTTP %s en %ss: %s", resp.status_code, elapsed, error_msg[:100])
                return f"[Erreur API] {error_msg}"
            
            # Gestion de la structure de réponse
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("Aucun choix dans la réponse LLM")
            
            content = choices[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            log.info("   ✅ LLM réponse en %ss | tokens: in=%s out=%s", elapsed, usage.get("prompt_tokens", "?"), usage.get("completion_tokens", "?"))
            return content
        except Exception as e:
            log.error("   ❌ LLM exception: %s", str(e)[:120])
            return f"[Erreur] {str(e)}"

    async def chat_with_tools(
        self,
        model: str,
        system: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
    ) -> dict:
        """Function calling natif OpenAI ; `chat()` reste inchangé.

        Retourne {"content": str, "tool_calls": list[dict], "error": Optional[str]}.
        """
        model = os.getenv("HAKIM_LLM_MODEL") or model
        estimated_tokens = max_tokens + len(system) // 4 + sum(len(m.get("content", "")) for m in messages) // 4
        await self.rate_limiter.acquire(estimated_tokens)

        body = {
            "model": model,
            "messages": [{"role": "system", "content": system}] + messages,
            "max_tokens": max_tokens,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": APP_REFERRER,
            "X-Title": APP_TITLE,
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            resp = await self.http.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=body,
            )
            text = resp.text
            
            # Parser la réponse de manière robuste
            data = None
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # Essayer de nettoyer si SSE
                if "data: [DONE]" in text:
                    text = text.split("data: [DONE]")[0].strip()
                start_idx = text.find("{")
                end_idx = text.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    text = text[start_idx : end_idx + 1]
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError as e:
                        log.error("Échec parsing JSON dans chat_with_tools: %s", str(e))
                        return {"content": "", "tool_calls": [], "error": f"[Tool API] Réponse JSON invalide"}
            
            if data is None:
                return {"content": "", "tool_calls": [], "error": f"[Tool API] Impossible de parser la réponse"}
            
            if resp.is_error:
                err = data.get("error", "")
                if isinstance(err, dict):
                    error_msg = err.get("message", str(resp.status_code))
                else:
                    error_msg = str(err) if err else str(resp.status_code)
                return {"content": "", "tool_calls": [], "error": f"[Tool API] {error_msg}"}
            
            # Extraire les choix
            choices = data.get("choices", [])
            if not choices:
                return {"content": "", "tool_calls": [], "error": "[Tool API] Aucun choix dans la réponse"}
            
            message = choices[0].get("message", {})
            content = message.get("content") or ""
            calls = []
            
            # Parser les appels d'outils (tool calls)
            for tc in message.get("tool_calls") or []:
                fn = tc.get("function") or {}
                try:
                    arguments = json.loads(fn.get("arguments") or "{}")
                except (json.JSONDecodeError, TypeError):
                    arguments = {}
                calls.append({
                    "id": tc.get("id", ""),
                    "name": fn.get("name", ""),
                    "arguments": arguments,
                })
            return {"content": content, "tool_calls": calls, "error": None}
        except Exception as e:
            log.error("Exception dans chat_with_tools: %s", str(e)[:120])
            return {"content": "", "tool_calls": [], "error": f"[Tool API] {str(e)}"}

    def is_configured(self) -> bool:
        return bool(self._api_key) or self.base_url != LOCAL_API_BASE

    async def close(self):
        await self.http.aclose()

    def _mock_response(self, model: str, system: str,
                       messages: list[dict]) -> str:
        last_msg = messages[-1]["content"] if messages else ""
        return (
            f"[APEX · Simulation {model}]\n\n"
            f"Configure OPENROUTER_API_KEY dans .env\n"
            f"---\nPrompt reçu:\n{last_msg[:200]}..."
        )


OpenChassisClient = LocalAPIClient
OpenRouterClient = LocalAPIClient

