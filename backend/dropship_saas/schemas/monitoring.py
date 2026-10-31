"""Monitoring schemas."""

from __future__ import annotations
from pydantic import BaseModel, Field


class ScheduleRequest(BaseModel):
    product_id: int
    interval_hours: int = Field(default=24, ge=1)
    alert_on_stock_drop: bool = True
    alert_on_price_change_percent: float = Field(default=10.0, ge=0.0, le=100.0)
    is_active: bool = True


class ScheduleResponse(BaseModel):
    id: int
    product_id: int
    interval_hours: int
    alert_on_stock_drop: bool
    alert_on_price_change_percent: float
    is_active: bool