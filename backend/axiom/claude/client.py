import os
import time
import asyncio
import httpx
import json
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from axiom.logging_setup import log
from axiom.core.circuit_breaker import (
    circuit_breakers,
    CircuitBreakerOpenException,
    LLMServiceUnavailableError,
)

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



OPENROUTER_MODEL_MAP = {
    "nemotron-3-ultra-free": "nvidia/nemotron-3-super-120b-a12b:free",
    "mimo-v2.5-free": "google/gemma-4-31b-it:free",
    "deepseek-v4-flash-free": "nvidia/nemotron-3.5-lightning:free",
    "minimax-m3-free": "google/gemma-4-26b-a4b-it:free",
    "qwen3.6-plus-free": "google/gemma-4-31b-it:free",
    "north-mini-code-free": "cohere/north-mini-code:free",
}


class LocalAPIClient:
    """Client API unifié : base résolue via HAKIM_LLM_BASE_URL,
    sinon OpenRouter si clé présente, sinon OPENCHASSIS_API_BASE (repli local),
    sinon la passerelle Console opencode."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        rpm: int = DEFAULT_RPM,
        tpm: int = DEFAULT_TPM,
    ):
        raw_openrouter_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
        is_placeholder = raw_openrouter_key in ("***", "sk-...", "your_api_key_here", "<votre-cle>", "")
        openrouter_key = "" if is_placeholder else raw_openrouter_key

        gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        if gemini_key in ("***", "<votre-cle>", "your_api_key_here"):
            gemini_key = ""

        omniroute_key = (os.getenv("OMNIROUTE_API_KEY") or "").strip()
        omniroute_base = (os.getenv("OMNIROUTE_BASE_URL") or "http://127.0.0.1:20128/v1").strip()

        self.base_url = (
            os.getenv("HAKIM_LLM_BASE_URL")
            or ("https://generativelanguage.googleapis.com/v1beta/openai" if gemini_key and not openrouter_key else OPENROUTER_API_BASE)
        )
        self._api_key = (
            os.getenv("HAKIM_LLM_API_KEY")
            or api_key
            or (gemini_key if "googleapis.com" in self.base_url else "")
            or (omniroute_key if "20128" in self.base_url else "")
            or (openrouter_key if "openrouter.ai" in self.base_url else "")
        )
        self.api_key = self._api_key
        self.http = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=2.0))
        self.rate_limiter = TokenBucketRateLimiter(rpm=rpm, tpm=tpm)

    def _resolve_target_endpoint(self, model: str) -> tuple[str, str, str]:
        """Résout (target_base_url, target_api_key, target_model) de manière sécurisée."""
        gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        omniroute_key = (os.getenv("OMNIROUTE_API_KEY") or "").strip()
        omniroute_base = (os.getenv("OMNIROUTE_BASE_URL") or "http://127.0.0.1:20128/v1").rstrip("/")
        openrouter_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
        is_placeholder = lambda k: not k or k in ("***", "sk-...", "your_api_key_here", "<votre-cle>")

        # 1. Requête ciblant explicitement OmniRoute
        if model.startswith("omniroute/") or model == "omniroute/local" or model.startswith("auto/"):
            target_model = "auto/best-fast" if model in ("omniroute/local", "omniroute/auto") else (
                model[len("omniroute/"):] if model.startswith("omniroute/") else model
            )
            return omniroute_base, omniroute_key or self._api_key, target_model

        # 2. Google Gemini AI Studio
        if "googleapis.com" in self.base_url or (gemini_key and not is_placeholder(gemini_key)):
            target_model = model
            if not target_model.startswith("gemini") or target_model == "gemini-2.5-flash":
                target_model = "gemini-3.5-flash"
            return "https://generativelanguage.googleapis.com/v1beta/openai", gemini_key or self._api_key, target_model

        # 3. OpenRouter / Autre
        target_model = OPENROUTER_MODEL_MAP.get(model, model)
        return OPENROUTER_API_BASE, openrouter_key or self._api_key, target_model

    def _build_candidate_chain(self, model: str) -> list[tuple[str, str, str, str]]:
        """Construit la liste ordonnée des modèles de secours : si un modèle échoue, on change."""
        candidates = []
        gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        omniroute_key = (os.getenv("OMNIROUTE_API_KEY") or "").strip()
        omniroute_base = (os.getenv("OMNIROUTE_BASE_URL") or "http://127.0.0.1:20128/v1").rstrip("/")

        # 1. Choix primaire demandé
        b_url, k, m_name = self._resolve_target_endpoint(model)
        candidates.append((b_url, k, m_name, model))

        # 2. Secours Google Gemini 3.5 Flash (ultra fiable)
        if gemini_key and (b_url != "https://generativelanguage.googleapis.com/v1beta/openai" or m_name != "gemini-3.5-flash"):
            candidates.append(("https://generativelanguage.googleapis.com/v1beta/openai", gemini_key, "gemini-3.5-flash", "gemini-3.5-flash"))

        # 3. Secours OmniRoute passerelle locale (781 modèles)
        if omniroute_base not in b_url:
            candidates.append((omniroute_base, omniroute_key, "auto/best-fast", "omniroute/auto/best-fast"))
            candidates.append((omniroute_base, omniroute_key, "auto/best-coding", "omniroute/auto/best-coding"))

        # 4. Secours OpenRouter
        raw_or_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
        if raw_or_key and raw_or_key not in ("***", "sk-..."):
            candidates.append((OPENROUTER_API_BASE, raw_or_key, "nvidia/nemotron-3-super-120b-a12b:free", "nemotron-free"))

        return candidates

    async def _execute_single_attempt(
        self, target_base_url: str, target_api_key: str, target_model: str,
        system: str, messages: list[dict], max_tokens: int
    ) -> str:
        """Exécute une tentative HTTP isolée."""
        body = {
            "model": target_model,
            "messages": [{"role": "system", "content": system}] + messages,
            "max_tokens": max_tokens,
        }
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": APP_REFERRER,
            "X-Title": APP_TITLE,
        }
        if target_api_key:
            headers["Authorization"] = f"Bearer {target_api_key}"

        t0 = time.time()
        resp = await self.http.post(
            f"{target_base_url}/chat/completions",
            headers=headers,
            json=body,
        )
        elapsed = round(time.time() - t0, 2)
        text = resp.text

        data = None
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            if "data: " in text:
                json_chunks = []
                for line in text.split("\n"):
                    line = line.strip()
                    if line.startswith("data: ") and not line.endswith("[DONE]"):
                        c_data = line[6:].strip()
                        if c_data:
                            try:
                                chunk = json.loads(c_data)
                                if isinstance(chunk, dict):
                                    json_chunks.append(chunk)
                            except Exception:
                                pass
                if json_chunks:
                    merged_choices = []
                    for chunk in json_chunks:
                        if "choices" in chunk:
                            for i, choice in enumerate(chunk["choices"]):
                                if i < len(merged_choices):
                                    if "delta" in choice:
                                        merged_choices[i]["message"]["content"] = (
                                            merged_choices[i].get("message", {}).get("content", "")
                                            + choice["delta"].get("content", "")
                                        )
                                else:
                                    merged_choices.append(choice)
                    data = {"choices": merged_choices}

        if data is None:
            raise ValueError(f"Réponse API non parseable: {text[:200]}")

        if isinstance(data, list):
            data = data[0] if data and isinstance(data[0], dict) else {}

        if resp.is_error:
            err = data.get("error", "")
            error_msg = err.get("message", str(resp.status_code)) if isinstance(err, dict) else str(err)
            raise LLMServiceUnavailableError(f"HTTP {resp.status_code}: {error_msg}", status_code=resp.status_code, model=target_model)

        choices = data.get("choices", [])
        if not choices:
            raise LLMServiceUnavailableError("Aucun choix retourné dans la réponse", model=target_model)

        msg = choices[0].get("message", {})
        content = msg.get("content")
        if not content:
            content = msg.get("reasoning") or msg.get("refusal") or ""
        content = str(content)
        usage = data.get("usage", {})
        log.info("   ✅ LLM [%s] réponse en %ss | in=%s out=%s tokens", target_model, elapsed, usage.get("prompt_tokens", "?"), usage.get("completion_tokens", "?"))
        return content

    async def chat(self, model: str, system: str,
                   messages: list[dict], max_tokens: int = 4096) -> str:
        model = model or os.getenv("HAKIM_LLM_MODEL") or "gemini-3.5-flash"
        if model == "auto":
            model = "gemini-3.5-flash"

        # Chaîne de bascule : si un modèle donne une erreur, on bascule automatiquement
        candidates = self._build_candidate_chain(model)
        last_error = None

        for b_url, k, m_name, label in candidates:
            breaker = circuit_breakers.get_or_create(f"llm:{label}")
            if not breaker.can_execute():
                log.info("🔌 Disjoncteur ouvert pour [%s] -> Changement automatique vers le modèle suivant", label)
                continue

            try:
                log.info("   📡 Appel LLM [%s] via %s...", label, b_url)
                content = await self._execute_single_attempt(b_url, k, m_name, system, messages, max_tokens)
                if content and content.strip():
                    breaker.record_success()
                    return content
            except Exception as e:
                is_429 = getattr(e, "status_code", None) == 429
                breaker.record_failure(error=e, is_rate_limit=is_429)
                last_error = e
                log.warning("   ⚠️ Erreur sur le modèle [%s] (%s). Changement de modèle immédiat...", label, str(e)[:120])
                continue

        # Si tous les modèles externes ont échoué, repli local de secours
        log.warning("⚠️ Tous les modèles distants sont en échec. Repli sur assistance locale...")
        return self._mock_response(model, system, messages)

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
        model = model or os.getenv("HAKIM_LLM_MODEL") or "gemini-2.5-flash"

        # Contrôle préalable par le Circuit Breaker
        breaker = circuit_breakers.get_or_create(f"llm:{model}")
        if not breaker.can_execute():
            log.warning("🔌 chat_with_tools bloqué par disjoncteur ouvert pour llm:%s", model)
            return {
                "content": "",
                "tool_calls": [],
                "error": f"CircuitBreakerOpen: Circuit ouvert pour '{model}' ({breaker.remaining_cooldown():.1f}s)",
            }

        estimated_tokens = max_tokens + len(system) // 4 + sum(len(m.get("content", "")) for m in messages) // 4
        await self.rate_limiter.acquire(estimated_tokens)

        # Résolution dynamique pour passerelle OmniRoute (Port 20128)
        target_base_url = self.base_url
        target_api_key = self._api_key
        target_model = model

        if model.startswith("omniroute/") or model == "omniroute/local" or model.startswith("auto/"):
            target_base_url = (os.getenv("OMNIROUTE_BASE_URL") or "http://127.0.0.1:20128/v1").rstrip("/")
            target_api_key = os.getenv("OMNIROUTE_API_KEY") or self._api_key
            if model == "omniroute/local":
                target_model = "auto/best-fast"
            elif model.startswith("omniroute/"):
                target_model = model[len("omniroute/"):]
            log.info("   ⚡ Routage Tools via OmniRoute Gateway (%s) → Modèle: %s", target_base_url, target_model)
        elif "googleapis.com" in target_base_url:
            if not target_model.startswith("gemini") or target_model == "gemini-2.5-flash":
                target_model = os.getenv("HAKIM_LLM_MODEL") or "gemini-3.5-flash"
                if not target_model.startswith("gemini") or target_model == "gemini-2.5-flash":
                    target_model = "gemini-3.5-flash"
                log.info("   🔮 Modèle Tools Google Gemini appliqué: %s", target_model)

        body = {
            "model": target_model,
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
        if target_api_key:
            headers["Authorization"] = f"Bearer {target_api_key}"

        try:
            resp = await self.http.post(
                f"{target_base_url}/chat/completions",
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
                is_429 = (resp.status_code == 429)
                breaker.record_failure(is_rate_limit=is_429)
                return {"content": "", "tool_calls": [], "error": f"[Tool API HTTP {resp.status_code}] {error_msg}"}
            
            # Extraire les choix
            choices = data.get("choices", [])
            if not choices:
                breaker.record_failure()
                return {"content": "", "tool_calls": [], "error": "[Tool API] Aucun choix dans la réponse"}
            
            message = choices[0].get("message", {})
            content = message.get("content") or message.get("reasoning") or ""
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
            breaker.record_success()
            return {"content": content, "tool_calls": calls, "error": None}
        except Exception as e:
            breaker.record_failure(error=e)
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

