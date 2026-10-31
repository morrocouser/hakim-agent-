"""
HERMES AGENT INTEGRATION — Orchestration layer

Features:
- URL data enrichment (product name, photos, description, attributes)
- Bulk orchestration (categories, stores)
- Multi-tenant isolation (Redis in-memory database + CELERY_BROKER_URL prefix)

The Hermes Agent handles logic that requires reasoning, while
Scrapling provides deterministic, reliable data extraction.
"""

from __future__ import annotations
import logging
import os
import json
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dropship_saas.hermes")

# Redis-based in-memory store for tenant-isolated data
REDIS_DATA_TTL = 3600  # 1 hour


def get_hermes_url() -> Optional[str]:
    """Get the Hermes Agent API URL if configured."""
    return os.environ.get("HERMES_AGENT_URL")


def get_hermes_api_key() -> Optional[str]:
    """Get the Hermes Agent API key if configured."""
    return os.environ.get("HERMES_AGENT_API_KEY")


def is_hermes_available() -> bool:
    """Check if Hermes Agent is configured and available."""
    return bool(get_hermes_url() and get_hermes_api_key())


async def enrich_product_with_hermes(
    payload: Dict[str, Any],
    tenant_id: str = "default",
) -> Dict[str, Any]:
    """
    Enrich product data with Hermes Agent.
    
    Hermes Agent can:
    - Rewrite product titles/descriptions for SEO
    - Generate variant attribute labels
    - Detect product categories
    - Suggest better product names
    
    This is a stub — in production, calls the Hermes Agent API.
    """
    if not is_hermes_available():
        logger.debug("Hermes Agent not configured — skipping enrichment")
        return payload
    
    # In production, this would call:
    # POST {HERMES_AGENT_URL}/v1/enrich
    # { "product_payload": payload, "tenant_id": tenant_id }
    
    logger.info(f"Enriching product {payload.get('source_id')} with Hermes Agent")
    return payload


async def orchestrate_bulk_scraping(
    category_url: str,
    platform: str,
    max_pages: int,
    tenant_id: str = "default",
) -> Dict[str, Any]:
    """
    Orchestrate bulk scraping with Hermes Agent.
    
    Hermes Agent handles:
    - Decision logic on which pages to scrape
    - Retry strategy on 429/captcha
    - Data validation before insertion
    """
    if not is_hermes_available():
        # Fallback to direct scraping without Hermes
        logger.warning("Hermes Agent not available — using direct scraping fallback")
        return await _direct_bulk_scrape(category_url, platform, max_pages)
    
    # In production, this would delegate to Hermes Agent
    logger.info(
        f"Orchestrating bulk scrape via Hermes Agent: "
        f"url={category_url}, platform={platform}, pages={max_pages}"
    )
    return await _direct_bulk_scrape(category_url, platform, max_pages)


async def _direct_bulk_scrape(
    category_url: str,
    platform: str,
    max_pages: int,
) -> Dict[str, Any]:
    """Direct bulk scraping fallback (without Hermes Agent)."""
    from dropship_saas.scraping.bulk import BulkScraper
    
    scraper = BulkScraper(platform)
    results = await scraper.scrape_category(category_url, max_pages=max_pages)
    
    return {
        "total_products": len(results),
        "products": results,
        "pages_processed": min(max_pages, len(results) + 1),
    }


def get_tenant_redis_key(tenant_id: str, key: str) -> str:
    """Get tenant-isolated Redis key."""
    return f"dropship:{tenant_id}:{key}"


async def store_scraped_data_in_redis(
    tenant_id: str,
    key: str,
    data: Any,
    ttl: int = REDIS_DATA_TTL,
) -> bool:
    """
    Store scraped data in tenant-isolated Redis namespace.
    
    This implements multi-tenant data isolation in memory.
    """
    import redis.asyncio as aioredis
    
    try:
        r = aioredis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        )
        full_key = get_tenant_redis_key(tenant_id, key)
        await r.setex(full_key, ttl, json.dumps(data, default=str))
        return True
    except Exception as e:
        logger.error(f"Redis store failed: {e}")
        return False


async def retrieve_scrapped_data_from_redis(
    tenant_id: str,
    key: str,
) -> Optional[Any]:
    """Retrieve scraped data from tenant-isolated Redis namespace."""
    import redis.asyncio as aioredis
    
    try:
        r = aioredis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        )
        full_key = get_tenant_redis_key(tenant_id, key)
        data = await r.get(full_key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Redis retrieve failed: {e}")
        return None
