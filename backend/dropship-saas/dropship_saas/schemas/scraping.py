"""Scraping schemas (request/response)."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from dropship_saas.schemas.product import ProductCreatePayload, ScrapingPayload


class ImportRequest(BaseModel):
    url: str = Field(..., min_length=1)
    platform: Optional[str] = None


class ImportResponse(BaseModel):
    job_id: Optional[str] = None
    payload: Optional[ProductCreatePayload] = None
    status: str = "pending"  # immediate or async
    message: str = "OK"


class BulkImportRequest(BaseModel):
    category_url: str = Field(..., min_length=1)
    max_pages: int = Field(default=10, ge=1, le=100)
    source_platform: Optional[str] = None


class BulkImportResponse(BaseModel):
    job_id: str
    total_products: int = 0
    status: str = "queued"