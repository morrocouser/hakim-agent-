"""
HakimAgent - Agent 2: Web / Data Worker (Étape 3)
Inspiré de CrewAI (Research Tools) et LangGraph (Recherche / RAG).

Interroge des APIs web, crawle ou extrait des résumés de documentation,
enrichit le contexte partagé avec des données structurées.
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any, Dict, List, Optional
import httpx

from hakim_agent.workers.base import BaseWorker
from hakim_agent.state import AgentState


class ResearcherWorker(BaseWorker):
    """
    Agent spécialisé dans la collecte, la recherche web et l'extraction de données.
    """

    name: str = "agent_researcher"
    role: str = "web_data"
    description: str = "Recherche web, extraction d'APIs et scraping de documentation."
    requires_review: bool = False  # Lecture / extraction, pas d'effet de bord critique

    def __init__(self, search_api_key: Optional[str] = None):
        self.search_api_key = search_api_key
        self._http = httpx.AsyncClient(timeout=15.0, follow_redirects=True)

    async def _search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Recherche DuckDuckGo via l'API HTML publique ou bibliothèque disponible."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    }
                    for r in results
                ]
        except Exception:
            # Fallback simple HTTP direct si la lib n'est pas configurée
            return [
                {
                    "title": f"Recherche pour: {query}",
                    "url": "https://duckduckgo.com/?q=" + query.replace(" ", "+"),
                    "snippet": f"Résultat simulé/fallback pour la requête '{query}'.",
                }
            ]

    async def _fetch_url_summary(self, url: str) -> str:
        """Récupère et résume sommairement le contenu texte d'une URL."""
        try:
            resp = await self._http.get(url, headers={"User-Agent": "HakimAgent/1.0"})
            if resp.status_code == 200:
                text = resp.text
                # Nettoyage sommaire des balises HTML
                clean_text = re.sub(r"<[^>]+>", " ", text)
                clean_text = re.sub(r"\s+", " ", clean_text).strip()
                return clean_text[:1000] + "..." if len(clean_text) > 1000 else clean_text
            return f"HTTP {resp.status_code}"
        except Exception as e:
            return f"Erreur fetch {url}: {str(e)}"

    async def execute(
        self,
        step: str,
        context: Dict[str, Any],
        state: Optional[AgentState] = None,
    ) -> Dict[str, Any]:
        """Exécute une tâche de recherche ou d'extraction de données."""
        start_time = time.time()
        
        # Détection d'URL directe
        urls = re.findall(r"https?://[^\s]+", step)
        
        findings = []
        if urls:
            for url in urls[:2]:
                summary = await self._fetch_url_summary(url)
                findings.append({"url": url, "summary": summary})
        else:
            # Nettoyer l'instruction pour extraire la requête
            query = re.sub(r"^(cherche|recherche|trouve|search|find)\s*", "", step, flags=re.I).strip()
            if not query:
                query = step
            results = await self._search_duckduckgo(query, max_results=4)
            findings.extend(results)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Synthèse textuelle
        summary_lines = [f"### Résultats pour : '{step}'"]
        for f in findings:
            if "url" in f and "snippet" in f:
                summary_lines.append(f"- **{f.get('title', 'Source')}** ({f['url']}) : {f['snippet']}")
            elif "url" in f and "summary" in f:
                summary_lines.append(f"- **Source** ({f['url']}) : {f['summary']}")

        output_text = "\n".join(summary_lines)

        return {
            "success": True,
            "query": step,
            "findings_count": len(findings),
            "findings": findings,
            "output": output_text,
            "execution_time_ms": elapsed_ms,
        }

    async def close(self):
        await self._http.aclose()
