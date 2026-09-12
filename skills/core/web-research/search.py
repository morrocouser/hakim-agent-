import urllib.request
import urllib.parse
import json


def search(query: str, num_results: int = 5) -> dict:
    """Search the web for information"""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json"

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        results = []

        if "RelatedTopics" in data:
            for topic in data["RelatedTopics"][:num_results]:
                if "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                    })

        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e), "results": [], "count": 0}
