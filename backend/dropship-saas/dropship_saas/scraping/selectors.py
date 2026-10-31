"""Dynamic selector engine — fallback-based extraction."""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dropship_saas.scraping.selectors")


class SelectorEngine:
    """Tries multiple CSS selectors, returns first non-empty match."""
    
    def __init__(self):
        self._empty_count = 0
        self._alert_threshold = 10
    
    def extract_with_fallback(
        self, html: str, selectors: List[str]
    ) -> Optional[str]:
        """Try selectors in order, return first non-empty result."""
        for selector in selectors:
            try:
                result = self._try_selector(html, selector)
                if result and result.strip():
                    return result.strip()
            except Exception:
                continue
        return None
    
    def _try_selector(self, html: str, selector: str) -> Optional[str]:
        """Try a single selector."""
        import re
        # Simple CSS selector → regex conversion for basic tags
        tag_match = re.match(r'(\w+)(?:\[([^\]]+)\])?', selector)
        if tag_match:
            tag = tag_match.group(1)
            attr = tag_match.group(2)
            if attr:
                pattern = rf'<{tag}[^>]*{attr}=["\']([^"\']+)["\'][^>]*>'
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    return match.group(1)
            else:
                pattern = rf'<{tag}[^>]*>(.*?)</{tag}>'
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1).strip()
        return None
    
    def check_health(self, is_empty: bool) -> str:
        """Track health and return status."""
        if is_empty:
            self._empty_count += 1
        else:
            self._empty_count = 0
        
        if self._empty_count >= self._alert_threshold:
            logger.warning(f"Health ALERT: {self._empty_count} consecutive empty results")
            return "alert"
        return "healthy"