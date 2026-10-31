"""Scraping API router — import endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from dropship_saas.database.session import get_db
from dropship_saas.database.models import ScrapingJob
from dropship_saas.schemas.scraping import (
    ImportRequest, ImportResponse, BulkImportRequest, BulkImportResponse
)
from dropship_saas.schemas.product import ProductCreatePayload
import uuid

router = APIRouter(prefix="/api/scraping", tags=["scraping"])


@router.post("/import", response_model=ImportResponse)
async def import_product(
    request: ImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import a single product by URL — triggers Scrapling extraction."""
    job_id = str(uuid.uuid4())
    
    # Create scraping job record
    job = ScrapingJob(
        id=job_id,
        url=request.url,
        source_platform=request.platform or "unknown",
        status="running",
        started_at=__import__("datetime").datetime.utcnow(),
    )
    db.add(job)
    await db.commit()
    
    # For MVP: synchronous extraction (will move to Celery)
    from dropship_saas.scraping.registry import get_scraper
    try:
        scraper = get_scraper(request.url)
        payload = scraper.fetch(request.url)
        
        # Save payload to job
        job.payload = payload
        job.status = "completed"
        job.completed_at = __import__("datetime").datetime.utcnow()
        await db.commit()
        
        return ImportResponse(
            job_id=job_id,
            payload=ProductCreatePayload(**payload),
            status="completed",
            message="Product imported successfully",
        )
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.completed_at = __import__("datetime").datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Scraping failed: {e}")


@router.post("/bulk", response_model=BulkImportResponse)
async def import_bulk(
    request: BulkImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Bulk import from category or store URL."""
    job_id = str(uuid.uuid4())
    
    job = ScrapingJob(
        id=job_id,
        url=request.category_url,
        source_platform=request.source_platform or "unknown",
        status="queued",
        started_at=__import__("datetime").datetime.utcnow(),
    )
    db.add(job)
    await db.commit()
    
    # Queue bulk scraping task (Celery)
    # from dropship_saas.tasks.scraping_tasks import scrape_bulk_category
    # scrape_bulk_category.delay(job_id, request.category_url, request.max_pages)
    
    return BulkImportResponse(
        job_id=job_id,
        total_products=0,
        status="queued",
    )


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Check scraping job status."""
    result = await db.execute(select(ScrapingJob).where(ScrapingJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "payload": job.payload,
        "error": job.error,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
    }