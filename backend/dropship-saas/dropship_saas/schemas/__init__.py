"""Pydantic schemas for dropship-saas."""

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class Currency(str, Enum):
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"


class ShippingSchema(BaseModel):
    cost: float
    min_days: int
    max_days: int


class VariantSchema(BaseModel):
    sku_source: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    cost_price: float
    in_stock: bool = True
    stock_quantity: int = 0


class ProductCreatePayload(BaseModel):
    """Payload for a single product scraped from a supplier."""
    source_platform: str
    source_id: str
    url: str
    currency: Currency = Currency.EUR
    base_title: str
    description: Optional[str] = None
    variants: list[VariantSchema] = Field(default_factory=list)
    shipping: Optional[ShippingSchema] = None
    images: list[str] = Field(default_factory=list)


class ProductOut(BaseModel):
    id: int
    supplier_id: int
    source_id: str
    url: str
    base_title: str
    description: Optional[str] = None
    currency: Currency = Currency.EUR
    status: str = "active"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VariantOut(BaseModel):
    id: int
    product_id: int
    sku_source: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    cost_price: float
    in_stock: bool = True
    stock_quantity: int = 0

    class Config:
        from_attributes = True


class PriceHistoryOut(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    price: float
    currency: Currency = Currency.EUR
    recorded_at: datetime

    class Config:
        from_attributes = True


class ScrapingPayload(BaseModel):
    """Matches CdC section 4.2 JSON schema."""
    source_platform: str
    source_id: str
    url: str
    currency: Currency = Currency.EUR
    base_title: str
    variants: list[dict] = Field(default_factory=list)
    shipping: Optional[dict] = None
    images: list[str] = Field(default_factory=list)


class ScrapingJobStatus(BaseModel):
    job_id: str
    status: str
    payload: Optional[ScrapingPayload] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None


class MonitoringSchedule(BaseModel):
    product_id: int
    interval_hours: int = 24
    alert_on_stock_drop: bool = True
    alert_on_price_change_percent: float = 10.0
    is_active: bool = True


class MonitoringStatus(BaseModel):
    product_id: int
    current_price: Optional[float] = None
    previous_price: Optional[float] = None
    price_change_percent: Optional[float] = None
    stock_quantity: int = 0
    in_stock: bool = True
    last_checked_at: Optional[datetime] = None
    status: str = "unknown"