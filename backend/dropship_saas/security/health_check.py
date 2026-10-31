"""Supplier health monitoring."""

from __future__ import annotations
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from dropship_saas.database.models import Supplier

logger = logging.getLogger("dropship_saas.security.health")


class SupplierHealthChecker:
    """Monitors supplier health based on consecutive empty scrape results."""
    
    def __init__(self, threshold: int = 10):
        self._threshold = threshold
    
    async def check_supplier_health(
        self, supplier_id: int, db: AsyncSession
    ) -> Dict[str, Any]:
        """Check health of a single supplier."""
        result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
        supplier = result.scalar_one_or_none()
        
        if not supplier:
            return {"status": "not_found", "supplier_id": supplier_id}
        
        if supplier.consecutive_empty >= self._threshold:
            return {
                "status": "alert",
                "supplier_id": supplier_id,
                "name": supplier.name,
                "consecutive_empty": supplier.consecutive_empty,
                "last_check_at": supplier.last_check_at,
                "message": f"Supplier in ALERT mode after {supplier.consecutive_empty} empty scrapes",
            }
        
        return {
            "status": "healthy",
            "supplier_id": supplier_id,
            "name": supplier.name,
            "consecutive_empty": supplier.consecutive_empty,
            "last_check_at": supplier.last_check_at,
        }
    
    async def get_health_report(self, db: AsyncSession) -> Dict[str, Any]:
        """Get health report for all suppliers."""
        result = await db.execute(select(Supplier))
        suppliers = result.scalars().all()
        
        report = {
            "total": len(suppliers),
            "healthy": 0,
            "alert": 0,
            "inactive": 0,
            "suppliers": [],
        }
        
        for supplier in suppliers:
            if not supplier.is_active:
                report["inactive"] += 1
                status = "inactive"
            elif supplier.consecutive_empty >= self._threshold:
                report["alert"] += 1
                status = "alert"
            else:
                report["healthy"] += 1
                status = "healthy"
            
            report["suppliers"].append({
                "id": supplier.id,
                "name": supplier.name,
                "status": status,
                "consecutive_empty": supplier.consecutive_empty,
                "last_check_at": supplier.last_check_at,
            })
        
        return report
    
    async def mark_empty_result(self, supplier_id: int, db: AsyncSession) -> None:
        """Increment consecutive empty counter for supplier."""
        result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
        supplier = result.scalar_one_or_none()
        if supplier:
            supplier.consecutive_empty += 1
            supplier.last_check_at = __import__("datetime").datetime.utcnow()
            await db.commit()
            
            if supplier.consecutive_empty >= self._threshold:
                logger.warning(
                    f"Supplier {supplier.name} ({supplier_id}) entering ALERT mode: "
                    f"{supplier.consecutive_empty} consecutive empty results"
                )
    
    async def mark_successful_result(self, supplier_id: int, db: AsyncSession) -> None:
        """Reset consecutive empty counter on successful scrape."""
        result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
        supplier = result.scalar_one_or_none()
        if supplier:
            supplier.consecutive_empty = 0
            supplier.last_check_at = __import__("datetime").datetime.utcnow()
            await db.commit()