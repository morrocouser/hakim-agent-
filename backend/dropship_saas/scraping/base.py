"""
SCRAPING BASE — Adapté pour Scrapling

⚠️ Ce module utilise des imports conditionnels pour scrapling.
Si scrapling n'est pas installé, les classes restent en mode "mock"
avec des stubs compatibles pour le développement/CI.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import os
import random
import time
from urllib.parse import urlparse
import logging

logger = logging.getLogger("dropship_saas.scraping")

# Import conditionnel : scrapling peut ne pas être disponible en dev
try:
    from scrapling import AdaptiveFetcher, AdaptiveParser
    HAS_SCRAPLING = True
except ImportError:
    HAS_SCRAPLING = False
    logger.warning("scrapling not installed — running in mock mode")

# Import requests comme fallback
import requests


class BaseScraper(ABC):
    """
    Base scraper avec mode adaptatif (stealth) et rate limiting.
    """
    
    def __init__(self):
        self._fetcher = None
        self._parser = None
        self._request_count = 0
        self._consecutive_empty = 0
        self._health_threshold = int(os.environ.get("SUPPLIER_HEALTH_THRESHOLD", "10"))
        self._delay_min = int(os.environ.get("SCRAPING_DELAY_MIN", "2"))
        self._delay_max = int(os.environ.get("SCRAPING_DELAY_MAX", "8"))
    
    def _apply_rate_limit(self) -> None:
        """Random delay between requests (2-8s) to avoid rate limits."""
        delay = random.uniform(self._delay_min, self._delay_max)
        logger.debug(f"Rate limit: sleeping {delay:.1f}s")
        time.sleep(delay)
    
    def _get_stealth_fetcher(self):
        """
        Retourne un AdaptiveFetcher avec TLS fingerprint emulation.
        Mode furtif pour simuler les empreintes navigateur.
        """
        if not HAS_SCRAPLING:
            return None
        try:
            self._fetcher = AdaptiveFetcher(
                adaptive=True,           # Mode adaptatif
                cache=True,              # Cache les réponses
                session=True,            # Réutilise la session
            )
            return self._fetcher
        except Exception as e:
            logger.warning(f"Could not create AdaptiveFetcher: {e}")
            return None
    
    def _get_parser(self, html: str):
        """Crée un parser adaptatif à partir du HTML."""
        if not HAS_SCRAPLING:
            return None
        try:
            self._parser = AdaptiveParser(html)
            return self._parser
        except Exception as e:
            logger.warning(f"Could not create AdaptiveParser: {e}")
            return None
    
    def _extract_with_selectors(self, html: str, selectors: List[str]) -> Optional[str]:
        """
        Extraction sélective avec fallback sur plusieurs sélecteurs.
        Si un sélecteur échoue, essaie le suivant.
        """
        if not HAS_SCRAPLING:
            return None
        
        parser = self._get_parser(html)
        if parser is None:
            return None
        
        for selector in selectors:
            try:
                result = parser.css(selector)
                if result and result.strip():
                    return result.strip()
            except Exception:
                continue
        return None
    
    def _check_health(self) -> bool:
        """Vérifie la santé du supplier. Retourne True si OK, False si alerte."""
        if self._consecutive_empty >= self._health_threshold:
            logger.warning(
                f"Supplier health ALERT: {self._consecutive_empty} consecutive empty results"
            )
            return False
        return True
    
    @abstractmethod
    def fetch(self, url: str) -> Dict[str, Any]:
        """Extract product data from URL. Returns payload matching CdC 4.2 schema."""
        self._apply_rate_limit()
        self._request_count += 1
    
    @abstractmethod
    def extract_title(self, html: str) -> str:
        """Extract product title."""
        pass
    
    @abstractmethod
    def extract_variants(self, html: str) -> List[Dict[str, Any]]:
        """Extract product variants (size, color, SKU, price, stock)."""
        pass
    
    @abstractmethod
    def extract_images(self, html: str) -> List[str]:
        """Extract HD image URLs."""
        pass
    
    @abstractmethod
    def extract_delivery(self, html: str) -> Dict[str, Any]:
        """Extract shipping cost and delivery estimates."""
        pass
    
    def reset_health(self) -> None:
        """Reset health counter on successful scrape."""
        self._consecutive_empty = 0
    
    def mark_empty(self) -> None:
        """Increment consecutive empty counter."""
        self._consecutive_empty += 1
        if not self._check_health():
            logger.error(f"Supplier entering ALERT mode after {self._consecutive_empty} failures")