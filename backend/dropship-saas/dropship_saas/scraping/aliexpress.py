"""AliExpress scraper — Scrapling-based extraction."""

from __future__ import annotations
import re
import logging
from typing import Any, Dict, List
from dropship_saas.scraping.base import BaseScraper

logger = logging.getLogger("dropship_saas.scraping.aliexpress")


class AliExpressScraper(BaseScraper):
    """Scraper for AliExpress product pages."""
    
    def __init__(self):
        super().__init__()
        self._source_platform = "aliexpress"
    
    def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch and extract product data from AliExpress URL."""
        super().fetch(url)
        
        try:
            # Try Scrapling first, fall back to requests
            if hasattr(self, '_fetcher') and self._fetcher is not None:
                response = self._fetcher.fetch(url)
                html = response.text
            else:
                import requests
                response = requests.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }, timeout=30)
                html = response.text
            
            if not html or len(html) < 100:
                self.mark_empty()
                raise ValueError(f"Empty response from {url}")
            
            # Extract data
            source_id = self._extract_source_id(url)
            title = self.extract_title(html)
            variants = self.extract_variants(html)
            images = self.extract_images(html)
            delivery = self.extract_delivery(html)
            
            self.reset_health()
            
            return {
                "source_platform": self._source_platform,
                "source_id": source_id,
                "url": url,
                "currency": "EUR",
                "base_title": title,
                "variants": variants,
                "shipping": delivery,
                "images": images,
            }
        except Exception as e:
            logger.error(f"AliExpress scrape failed for {url}: {e}")
            self.mark_empty()
            raise
    
    def _extract_source_id(self, url: str) -> str:
        """Extract product ID from AliExpress URL."""
        match = re.search(r'/item/(\d+)', url)
        if match:
            return match.group(1)
        return url  # fallback to full URL
    
    def extract_title(self, html: str) -> str:
        """Extract product title from HTML."""
        # AliExpress uses various title selectors
        selectors = [
            'h1[data-spu-title]',
            'h1.product-title',
            'h1.title',
            'title',
        ]
        for selector in selectors:
            match = re.search(
                rf'<{selector}[^>]*>(.*?)</{selector}>',
                html, re.IGNORECASE | re.DOTALL
            )
            if match:
                return match.group(1).strip()
        return "Unknown Product"
    
    def extract_variants(self, html: str) -> List[Dict[str, Any]]:
        """Extract product variants (size, color, SKU, price, stock)."""
        variants = []
        # Look for variant data in JSON-LD or inline scripts
        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>',
            html, re.DOTALL
        )
        if match:
            import json
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict):
                    offers = data.get("offers", [])
                    if isinstance(offers, list):
                        for offer in offers:
                            variants.append({
                                "sku_source": offer.get("sku", f"SKU-{len(variants)}"),
                                "attributes": {"name": offer.get("title", "Default")},
                                "cost_price": float(offer.get("price", 0)),
                                "in_stock": offer.get("availability", "InStock") == "InStock",
                                "stock_quantity": 1,
                            })
            except Exception:
                pass
        
        # Fallback: extract from variant selector blocks
        if not variants:
            variant_blocks = re.findall(
                r'<div[^>]*class="[^"]*variant[^"]*"[^>]*>(.*?)</div>',
                html, re.DOTALL
            )
            for block in variant_blocks:
                sku_match = re.search(r'data-sku="([^"]*)"', block)
                price_match = re.search(r'data-price="([^"]*)"', block)
                stock_match = re.search(r'data-stock="([^"]*)"', block)
                if sku_match:
                    variants.append({
                        "sku_source": sku_match.group(1),
                        "attributes": {"name": f"Variant {len(variants)}"},
                        "cost_price": float(price_match.group(1)) if price_match else 0.0,
                        "in_stock": stock_match is not None and int(stock_match.group(1) or 0) > 0,
                        "stock_quantity": int(stock_match.group(1)) if stock_match else 0,
                    })
        
        return variants
    
    def extract_images(self, html: str) -> List[str]:
        """Extract HD image URLs."""
        images = []
        # AliExpress stores images in various formats
        # Look for image URLs in JSON-LD, meta tags, or inline scripts
        img_matches = re.findall(
            r'https?://[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*',
            html, re.IGNORECASE
        )
        for img in img_matches:
            if "aliexpress" in img or "alicdn" in img:
                images.append(img)
        return images[:10]  # Limit to 10 images
    
    def extract_delivery(self, html: str) -> Dict[str, Any]:
        """Extract shipping cost and delivery estimates."""
        # Default values
        delivery = {"cost": 0.0, "min_days": 7, "max_days": 12}
        
        # Look for shipping info in JSON-LD
        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>',
            html, re.DOTALL
        )
        if match:
            import json
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict):
                    shipping_info = data.get("shippingDetails", {})
                    if shipping_info:
                        cost = float(shipping_info.get("shippingCost", 0))
                        delivery["cost"] = cost
            except Exception:
                pass
        
        return delivery