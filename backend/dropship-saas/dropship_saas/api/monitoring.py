"""Monitoring API router — schedule monitoring jobs."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from dropship_saas.database.session import get_db
from dropship_saas.schemas.monitoring import ScheduleRequest, ScheduleResponse

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.post("/schedule")
async def create_monitoring_schedule(
    request: ScheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a monitoring schedule for a product."""
    from dropship_saas.database.models import Product
    result = await db.execute(select(Product).where(Product.id == request.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Create monitoring schedule
    # In this MVP we'll just return the schedule (full DB model in Sprint 4)
    return {
        "product_id": request.product_id,
        "interval_hours": request.interval_hours,
        "alert_on_stock_drop": request.alert_on_stock_drop,
        "alert_on_price_change_percent": request.alert_on_price_change_percent,
        "is_active": request.is_active,
    }


@router.get("/status/{product_id}")
async def get_monitoring_status(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get current monitoring status for a product."""
    from dropship_saas.database.models import Product, PriceHistory, ProductVariant
    from datetime import datetime, timedelta
    
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get latest variant price
    var_result = await db.execute(
        select(ProductVariant).where(ProductVariant.product_id == product_id)
    )
    variants = var_result.scalars().all()
    
    # Get latest price history entry
    latest_price = None
    latest_variant_price = None
    if variants:
        # Get latest price for the product
        price_result = await db.execute(
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.recorded_at.desc())
            .limit(2)
        )
        prices = price_result.scalars().all()
        if prices:
            latest_price = prices[0]
            previous_price = prices[1] if len(prices) > 1 else None
        else:
            latest_price = None
            previous_price = None
    
    return {
        "product_id": product_id,
        "current_price": latest_price.price if latest_price else None,
        "previous_price": previous_price.price if previous_price else None,
        "price_change_percent": (
            ((latest_price.price - previous_price.price) / previous_price.price) * 100
            if latest_price and previous_price and previous_price.price > 0
            else None
        ),
        "stock_quantity": sum(v.stock_quantity for v in variants),
        "in_stock": any(v.in_stock for v in variants),
        "last_checked_at": latest_price.recorded_at if latest_price else None,
        "status": "healthy" if any(v.in_stock for v in variants) else "out_of_stock",
    }