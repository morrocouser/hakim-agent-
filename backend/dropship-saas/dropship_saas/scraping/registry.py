"""
Scraping registry and factory functions.
"""

from dropship_saas.scraping.base import BaseScraper
from dropship_saas.scraping.aliexpress import AliExpressScraper
from dropship_saas.scraping.amazon import AmazonScraper
from typing import Dict, Type
import re


class ScraperFactory:
    """Factory for creating and managing scrapers."""
    
    # Registry of platform -> scraper class
    SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {
        "aliexpress": AliExpressScraper,
        "amazon": AmazonScraper,
        "amazon.fr": AmazonScraper,
        "cdiscount": None,
        "temu": None,
        "shein": None,
        "cjdropshipping": None,
    }
    
    def __init__(self):
        pass
    
    def get_scraper(self, url: str):
        """Returns the appropriate scraper instance for a URL."""
        url_lower = url.lower()
        
        if "aliexpress.com" in url_lower:
            return AliExpressScraper()
        elif "amazon" in url_lower and ".fr" in url_lower:
            return AmazonScraper()
        elif "amazon." in url_lower:
            return AmazonScraper()
        else:
            raise ValueError(f"Unsupported source platform for URL: {url}")
    
    def list_scrapers(self):
        """List all registered scraper platforms."""
        return [k for k, v in self.SCRAPER_REGISTRY.items() if v is not None]


# Backward compatibility functions
def get_scraper(url: str):
    factory = ScraperFactory()
    return factory.get_scraper(url)


def detect_platform(url: str) -> str:
    """Detect platform name from URL."""
    factory = ScraperFactory()
    scraper = factory.get_scraper(url)
    return scraper._source_platform