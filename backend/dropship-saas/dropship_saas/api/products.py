"""Products API router — CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from dropship_saas.database.session import get_db
from dropship_saas.database.models import Product, ProductVariant, PriceHistory, DeliveryEstimate
from dropship_saas.schemas.product import ProductOut, VariantOut, ProductCreatePayload

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=List[ProductOut])
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List products with pagination."""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Product)
        .offset(offset)
        .limit(page_size)
        .order_by(Product.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get product by ID with variants and price history."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreatePayload,
    db: AsyncSession = Depends(get_db),
):
    """Create product from scraping payload."""
    from dropship_saas.database.models import Supplier
    
    # Get or create supplier
    supplier_result = await db.execute(
        select(Supplier).where(Supplier.name == payload.source_platform)
    )
    supplier = supplier_result.scalar_one_or_none()
    if not supplier:
        supplier = Supplier(
            name=payload.source_platform,
            base_url=payload.url,
            is_active=True,
        )
        db.add(supplier)
        await db.flush()
    
    # Create product
    product = Product(
        supplier_id=supplier.id,
        source_id=payload.source_id,
        url=payload.url,
        base_title=payload.base_title,
        description=payload.description,
        currency=payload.currency.value,
        status="active",
    )
    db.add(product)
    await db.flush()
    
    # Create variants
    for variant_data in payload.variants:
        variant = ProductVariant(
            product_id=product.id,
            sku_source=variant_data.sku_source,
            attributes=variant_data.attributes,
            cost_price=variant_data.cost_price,
            in_stock=variant_data.in_stock,
            stock_quantity=variant_data.stock_quantity,
        )
        db.add(variant)
    
    # Create delivery estimate if provided
    if payload.shipping:
        delivery = DeliveryEstimate(
            product_id=product.id,
            cost=payload.shipping.cost,
            min_days=payload.shipping.min_days,
            max_days=payload.shipping.max_days,
        )
        db.add(delivery)
    
    await db.commit()
    await db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    payload: ProductCreatePayload,
    db: AsyncSession = Depends(get_db),
):
    """Update product (edit text, photos, pricing)."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.base_title = payload.base_title
    product.description = payload.description
    product.currency = payload.currency.value
    product.updated_at = datetime.utcnow()
    
    # Update variants - simple approach: replace all
    await db.execute(
        ProductVariant.__table__.delete().where(ProductVariant.product_id == product_id)
    )
    for variant_data in payload.variants:
        variant = ProductVariant(
            product_id=product.id,
            sku_source=variant_data.sku_source,
            attributes=variant_data.attributes,
            cost_price=variant_data.cost_price,
            in_stock=variant_data.in_stock,
            stock_quantity=variant_data.stock_quantity,
        )
        db.add(variant)
    
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.status = "discontinued"
    product.updated_at = datetime.utcnow()
    await db.commit()


@router.get("/{product_id}/variants", response_model=List[VariantOut])
async def list_variants(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List variants for a product."""
    result = await db.execute(
        select(ProductVariant).where(ProductVariant.product_id == product_id)
    )
    return result.scalars().all()


@router.post("/{product_id}/sync-woocommerce", status_code=status.HTTP_202_ACCEPTED)
async def sync_to_woocommerce(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Push product to WooCommerce (AliDropship)."""
    from dropship_saas.api.woocommerce import is_woocommerce_configured
    from dropship_saas.api.woocommerce import build_wc_product_payload
    from dropship_saas.api.woocommerce import get_wc_client
    
    if not is_woocommerce_configured():
        raise HTTPException(
            status_code=503,
            detail="WooCommerce not configured. Set WOOCOMMERCE_URL, "
                   "WOOCOMMERCE_CONSUMER_KEY, WOOCOMMERCE_CONSUMER_SECRET"
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
        else:
            # Create new
            response = await client.post("/products", json=payload)
        
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
    
    # Update price history
    history = PriceHistory(
        product_id=product.id,
        variant_id=variants[0].id,
        price=variants[0].cost_price,
        currency=product.currency,
        recorded_at=datetime.utcnow(),
    )
    db.add(history)
    
    await db.commit()
    
    return {
        "message": f"Product synced to WooCommerce",
        "woocommerce_id": wc_id,
        "product_id": product_id,
    }