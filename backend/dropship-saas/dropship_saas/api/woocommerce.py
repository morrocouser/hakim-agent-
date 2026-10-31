"""
WooCommerce / AliDropship Integration API
Push products to WooCommerce store and handle order webhooks.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import httpx
import os
import logging

from dropship_saas.database.session import get_db
from dropship_saas.database.models import Product, ProductVariant, Supplier
from dropship_saas.schemas.product import ProductOut
from dropship_saas.security.encryption import decrypt_token
router = APIRouter(prefix="/api/woocommerce", tags=["woocommerce"])
log = logging.getLogger("dropship_saas.woocommerce")

# WooCommerce REST API base
WC_BASE_URL = os.environ.get("WOOCOMMERCE_URL")  # e.g., https://your-store.com/wp-json/wc/v3
WC_CONSUMER_KEY = os.environ.get("WOOCOMMERCE_CONSUMER_KEY")
WC_CONSUMER_SECRET = os.environ.get("WOOCOMMERCE_CONSUMER_SECRET")


def get_wc_auth():
    """Get HTTP Basic Auth tuple for WooCommerce API."""
    if not WC_CONSUMER_KEY or not WC_CONSUMER_SECRET:
        return None
    return (WC_CONSUMER_KEY, WC_CONSUMER_SECRET)


def is_woocommerce_configured() -> bool:
    """Check if WooCommerce credentials are configured."""
    base_url = os.environ.get("WOOCOMMERCE_URL")
    consumer_key = os.environ.get("WOOCOMMERCE_CONSUMER_KEY")
    consumer_secret = os.environ.get("WOOCOMMERCE_CONSUMER_SECRET")
    return bool(base_url and consumer_key and consumer_secret)


async def get_wc_client() -> Optional[httpx.AsyncClient]:
    """Create authenticated WooCommerce client."""
    if not is_woocommerce_configured():
        return None
    auth = get_wc_auth()
    return httpx.AsyncClient(
        base_url=WC_BASE_URL.rstrip("/"),
        auth=auth,
        timeout=30.0,
        headers={"User-Agent": "AliDropship-SaaS/1.0"},
    )


def build_wc_product_payload(product: Product, variants: List[ProductVariant]) -> dict:
    """Build WooCommerce product payload from our product model."""
    # Map our variants to WC variations
    wc_variations = []
    for v in variants:
        wc_variations.append({
            "sku": v.sku_source,
            "regular_price": str(v.cost_price * 2.5),  # 2.5x markup default
            "manage_stock": True,
            "stock_quantity": v.stock_quantity or 0,
            "in_stock": v.in_stock,
            "attributes": [
                {"name": k, "option": str(val)} 
                for k, val in (v.attributes or {}).items()
            ] if v.attributes else [],
        })
    
    return {
        "name": product.base_title,
        "type": "variable" if len(wc_variations) > 1 else "simple",
        "description": product.description or "",
        "short_description": (product.description or "")[:200],
        "sku": product.source_id,
        "regular_price": str(variants[0].cost_price * 2.5) if variants else "0",
        "manage_stock": True,
        "stock_quantity": sum(v.stock_quantity or 0 for v in variants),
        "in_stock": any(v.in_stock for v in variants),
        "categories": [{"name": "AliExpress Import"}],
        "tags": ["dropshipping", "aliexpress", "auto-import"],
        "images": [],  # Would need image URLs from product
        "attributes": [] if len(wc_variations) <= 1 else [
            {
                "name": k,
                "options": list(set(str(v.attributes.get(k, "")) for v in variants if v.attributes and k in v.attributes)),
                "visible": True,
                "variation": True,
            }
            for k in set().union(*[set(v.attributes.keys()) for v in variants if v.attributes])
        ],
        "variations": wc_variations if len(wc_variations) > 1 else [],
        "meta_data": [
            {"key": "_ali_source_id", "value": product.source_id},
            {"key": "_ali_source_url", "value": product.url or ""},
            {"key": "_ali_supplier", "value": product.supplier.name if product.supplier else "unknown"},
            {"key": "_ali_imported_at", "value": product.created_at.isoformat() if product.created_at else ""},
        ],
    }


@router.post("/{product_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_product_to_woocommerce(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Push a product to WooCommerce (AliDropship)."""
    if not is_woocommerce_configured():
        raise HTTPException(
            status_code=503,
            detail="WooCommerce not configured. Set WOOCOMMERCE_URL, WOOCOMMERCE_CONSUMER_KEY, WOOCOMMERCE_CONSUMER_SECRET"
        )
    
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Load variants
    variants_result = await db.execute(
        select(ProductVariant).where(ProductVariant.product_id == product_id)
    )
    variants = variants_result.scalars().all()
    
    if not variants:
        raise HTTPException(status_code=400, detail="Product has no variants to sync")
    
    payload = build_wc_product_payload(product, variants)
    
    async with await get_wc_client() as client:
        # Check if product already exists by SKU
        existing = await client.get(f"/products?sku={product.source_id}")
        if existing.status_code == 200 and existing.json():
            wc_product_id = existing.json()[0]["id"]
            # Update existing
            response = await client.put(f"/products/{wc_product_id}", json=payload)
            action = "updated"
        else:
            # Create new
            response = await client.post("/products", json=payload)
            action = "created"
        
        if response.status_code not in (200, 201):
            log.error(f"WooCommerce sync failed: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=502,
                detail=f"WooCommerce API error: {response.status_code}"
            )
        
        wc_product = response.json()
        wc_id = wc_product["id"]
    
    # Update our product with WooCommerce ID
    product.meta_data = product.meta_data or {}
    product.meta_data["woocommerce_id"] = wc_id
    product.meta_data["woocommerce_sync_status"] = "synced"
    product.meta_data["woocommerce_last_sync"] = datetime.utcnow().isoformat()
    product.updated_at = datetime.utcnow()
    await db.commit()
    
    return {
        "message": f"Product {action} in WooCommerce",
        "woocommerce_id": wc_id,
        "product_id": product_id,
        "action": action,
    }


@router.post("/bulk-sync", status_code=status.HTTP_202_ACCEPTED)
async def bulk_sync_products(
    product_ids: List[int],
    db: AsyncSession = Depends(get_db),
):
    """Sync multiple products to WooCommerce."""
    if not is_woocommerce_configured():
        raise HTTPException(
            status_code=503,
            detail="WooCommerce not configured"
        )
    
    results = []
    for pid in product_ids:
        try:
            result = await sync_product_to_woocommerce(pid, db)
            results.append({"product_id": pid, "status": "success", **result})
        except HTTPException as e:
            results.append({"product_id": pid, "status": "error", "detail": e.detail})
    
    return {"results": results, "total": len(results)}


@router.post("/webhook/order", status_code=status.HTTP_200_OK)
async def woocommerce_order_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    WooCommerce order webhook - receive new orders from AliDropship store.
    Configure in WooCommerce: Settings > Advanced > Webhooks > Add webhook
    Topic: order.created, Delivery URL: https://your-api.com/api/woocommerce/webhook/order
    """
    payload = await request.json()
    
    # Verify webhook secret if configured
    webhook_secret = os.environ.get("WOOCOMMERCE_WEBHOOK_SECRET")
    if webhook_secret:
        # WooCommerce sends X-WC-Webhook-Signature header
        signature = request.headers.get("X-WC-Webhook-Signature")
        if not signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        # TODO: Verify HMAC signature
    
    order_id = payload.get("id")
    line_items = payload.get("line_items", [])
    customer = payload.get("billing", {})
    
    log.info(f"Received WooCommerce order #{order_id} with {len(line_items)} items")
    
    # Process each line item - create fulfillment task
    for item in line_items:
        product_id = item.get("product_id")
        variation_id = item.get("variation_id")
        quantity = item.get("quantity", 1)
        
        # Find our product by WooCommerce ID
        result = await db.execute(
            select(Product).where(
                Product.meta_data.op('->>')('woocommerce_id') == str(product_id)
            )
        )
        product = result.scalar_one_or_none()
        
        if product:
            log.info(f"Order item maps to our product {product.id} (SKU: {product.source_id})")
            # TODO: Queue fulfillment task to AliExpress
            # from dropship_saas.tasks.fulfillment import fulfill_order
            # fulfill_order.delay(product.id, variation_id, quantity, customer)
        else:
            log.warning(f"No local product found for WC product_id={product_id}")
    
    return {"status": "received", "order_id": order_id, "items_processed": len(line_items)}


@router.get("/status")
async def woocommerce_status():
    """Check WooCommerce connection status."""
    if not is_woocommerce_configured():
        return {
            "configured": False,
            "message": "WooCommerce credentials not set"
        }
    
    async with await get_wc_client() as client:
        try:
            response = await client.get("/system_status")
            if response.status_code == 200:
                return {
                    "configured": True,
                    "connected": True,
                    "store_url": WC_BASE_URL,
                    "version": response.json().get("version", "unknown"),
                }
        except Exception as e:
            log.error(f"WooCommerce connection test failed: {e}")
    
    return {
        "configured": True,
        "connected": False,
        "error": "Could not connect to WooCommerce API",
    }