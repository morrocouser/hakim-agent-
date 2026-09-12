import urllib.request
import urllib.parse
import json


def fact_check(statement: str) -> dict:
    """Verify a statement against trusted sources"""
    try:
        encoded_query = urllib.parse.quote(statement)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json"

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        sources = []
        confidence = 0.5

        if "RelatedTopics" in data:
            for topic in data["RelatedTopics"][:3]:
                if "Text" in topic:
                    sources.append({
                        "text": topic["Text"][:200],
                        "url": topic.get("FirstURL", ""),
                    })

        if len(sources) >= 3:
            confidence = 0.8
        elif len(sources) >= 1:
            confidence = 0.6

        return {
            "statement": statement,
            "confidence": confidence,
            "sources": sources,
            "verdict": "Supported" if confidence > 0.7 else "Unverified",
        }
    except Exception as e:
        return {
            "statement": statement,
            "confidence": 0.0,
            "sources": [],
            "verdict": "Error",
            "error": str(e),
        }
