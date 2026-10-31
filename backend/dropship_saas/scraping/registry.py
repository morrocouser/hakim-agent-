"""Scraping registry and factory functions."""

from dropship_saas.scraping.base import BaseScraper
from dropship_saas.scraping.aliexpress import AliExpressScraper
from dropship_saas.scraping.amazon import AmazonScraper
from typing import Dict, Type
import re

# Registry of platform -> scraper class
SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {
    "aliexpress": AliExpressScraper,
    "amazon": AmazonScraper,
    "amazon.fr": AmazonScraper,
    "cdiscount": None,  # Future
    "temu": None,  # Future
    "shein": None,  # Future
    "cjdropshipping": None,  # Future
}


def get_scraper(url: str) -> BaseScraper:
    """
    Factory function: returns the appropriate scraper instance for a URL.
    
    Usage:
        scraper = get_scraper("https://www.aliexpress.com/item/123.html")
        payload = scraper.fetch(url)
    """
    url_lower = url.lower()
    
    # Match by domain patterns
    if "aliexpress.com" in url_lower:
        return AliExpressScraper()
    elif "amazon" in url_lower and ".fr" in url_lower:
        return AmazonScraper()
    elif "amazon." in url_lower:
        return AmazonScraper()
    else:
        raise ValueError(f"Unsupported source platform for URL: {url}")


def detect_platform(url: str) -> str:
    """Detect platform name from URL."""
    url_lower = url.lower()
    for platform in SCRAPER_REGISTRY:
        if platform in url_lower:
            return platform
    raise ValueError(f"Cannot detect platform for URL: {url}")