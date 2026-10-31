"""Main FastAPI application setup for dropship-saas."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

import os
import logging

log = logging.getLogger("dropship_saas.api")

# Rate limiter: optional via ENABLE_RATE_LIMIT env var (default off for local dev)
_enable_rate_limiting = os.environ.get("ENABLE_RATE_LIMIT", "0").lower() in {"1", "true", "yes"}
if _enable_rate_limiting:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None


# Allowed origins for CORS - strict list, no wildcards
cors_origins_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
cors_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management."""
    log.info("Dropship SaaS API starting")
    if limiter is not None:
        log.info("Rate limiting enabled")
    yield
    log.info("Dropship SaaS API shutting down")


app = FastAPI(title="Dropship SaaS API", lifespan=lifespan)

# CORS configuration - strict origins only (no wildcards)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to every response."""
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    # HSTS: only when using HTTPS or explicitly requested for testing
    if request.url.scheme == "https" or os.environ.get("FORCE_HSTS") == "1":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


# Rate limit exception handler (only if rate limiting is enabled)
if limiter is not None:
    from slowapi.errors import RateLimitExceeded
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return Response("Rate limit exceeded", status_code=429)


# Import routers
from dropship_saas.api.products import router as products_router
from dropship_saas.api.scraping import router as scraping_router
from dropship_saas.api.monitoring import router as monitoring_router
from dropship_saas.api.woocommerce import router as woocommerce_router

app.include_router(products_router)
app.include_router(scraping_router)
app.include_router(monitoring_router)
app.include_router(woocommerce_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "dropship-saas"}


@app.get("/")
async def root():
    return {"message": "Dropship SaaS API - MVP"}