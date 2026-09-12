import urllib.request
import re


def extract(url: str) -> dict:
    """Extract content from a URL"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")

        # Remove script and style tags
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)

        # Extract text content
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()

        # Extract title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE)
        title = title_match.group(1) if title_match else "No title"

        # Extract meta description
        desc_match = re.search(
            r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html, re.IGNORECASE
        )
        description = desc_match.group(1) if desc_match else ""

        return {
            "title": title,
            "description": description,
            "content": text[:5000],
            "url": url,
        }
    except Exception as e:
        return {"error": str(e), "url": url}
