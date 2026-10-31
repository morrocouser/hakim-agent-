"""Bulk scraping — category/store extraction."""

from __future__ import annotations
import logging
from typing import Any, Dict, List
from dropship_saas.scraping.aliexpress import AliExpressScraper
from dropship_saas.scraping.amazon import AmazonScraper

logger = logging.getLogger("dropship_saas.scraping.bulk")


class BulkScraper:
    """Bulk extractor for categories and seller stores."""
    
    def __init__(self, scraper=None):
        self._scraper = scraper or AliExpressScraper()
        self._products: List[Dict[str, Any]] = []
    
    def scrape_category(
        self, category_url: str, max_pages: int = 50
    ) -> List[Dict[str, Any]]:
        """Scrape all products in a category with pagination."""
        self._products = []
        for page in range(1, max_pages + 1):
            page_url = f"{category_url}&page={page}" if "page=" not in category_url else category_url
            try:
                products = self._scraper.fetch(page_url)
                if not products:
                    break
                self._products.extend(products)
                logger.info(f"Category page {page}: {len(products)} products")
            except Exception as e:
                logger.error(f"Category scrape failed on page {page}: {e}")
                break
        return self._products
    
    def scrape_store(self, seller_url: str) -> List[Dict[str, Any]]:
        """Scrape all products from a seller's store."""
        self._products = []
        try:
            products = self._scraper.fetch(seller_url)
            self._products.extend(products)
        except Exception as e:
            logger.error(f"Store scrape failed: {e}")
        return self._products