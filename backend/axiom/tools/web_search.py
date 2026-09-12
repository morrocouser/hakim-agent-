from __future__ import annotations

import httpx
from typing import Optional


class WebSearchTool:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""
        self.http = httpx.AsyncClient(timeout=30)

    async def search(self, query: str, max_results: int = 5) -> str:
        if not self.api_key:
            return (
                "[Recherche web indisponible]\n"
                "Configure WEB_SEARCH_API_KEY dans .env pour activer la recherche."
            )
        try:
            resp = await self.http.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": self.api_key,
                },
                params={"q": query, "count": max_results},
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for r in data.get("web", {}).get("results", [])[:max_results]:
                title = r.get("title", "")
                url = r.get("url", "")
                desc = r.get("description", "")
                results.append(f"- {title}\n  {url}\n  {desc}")
            return "\n\n".join(results) if results else "Aucun résultat trouvé."
        except Exception as e:
            return f"[Erreur recherche web] {str(e)}"

    async def close(self):
        await self.http.aclose()
