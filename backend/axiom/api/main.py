import uvicorn
import os
import time
from urllib.parse import urlparse
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from axiom.api.routes import router
from axiom.api.auth_routes import router as auth_router
from axiom.api.conversation_routes import router as convo_router
from axiom.db.models import DatabaseManager, init_db, close_db
from axiom.logging_setup import log
from middleware.rate_limiting import (
    ClientIdentifier,
    RateLimitConfig,
    create_rate_limiter,
    get_default_rate_limit_for_endpoint,
)


# =============================================================================
# LIFESPAN MANAGEMENT (remplace @app.on_event déprécié)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gère le lifecycle de l'application.
    
    Remplace @app.on_event("startup") et @app.on_event("shutdown")
    qui sont dépréciés dans les versions récentes de FastAPI.
    """
    # Startup
    await DatabaseManager.init_db()
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("🚀 APEX v4.0 — Serveur démarré")
    log.info("   API: http://localhost:8000")
    log.info("   Docs: http://localhost:8000/docs")
    log.info("   Auth: /auth/login | /auth/register")
    log.info("   Conversations: /api/conversations")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    yield
    
    # Shutdown
    await DatabaseManager.close_db()


# ---- Rate limit configuration (env-driven) ----
RATE_LIMIT_PER_MIN = int(os.getenv("HAKIM_RATE_LIMIT_PER_MIN", "60"))
RATE_LIMIT_REDIS_URL = os.getenv("HAKIM_RATE_LIMIT_REDIS_URL", "").strip()

_redis_config = None
if RATE_LIMIT_REDIS_URL:
    parsed = urlparse(RATE_LIMIT_REDIS_URL)
    _redis_config = {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 6379,
        "db": int((parsed.path or "/0").lstrip("/") or 0),
        "password": parsed.password,
    }

rate_limiter = create_rate_limiter(use_redis=bool(_redis_config), redis_config=_redis_config)
log.info(
    "Rate limiter: %s (limit=%d req/min per IP)",
    type(rate_limiter).__name__,
    RATE_LIMIT_PER_MIN,
)

app = FastAPI(
    title="APEX v4.0 — Agent Orchestrateur Multi-Modèle",
    version="4.0.0",
    description="API d'orchestration multi-agents avec scoring algorithmique et routage intelligent",
    lifespan=lifespan,
)

# Configuration CORS — par défaut restreint (pas de wildcard en prod).
# Définir HAKIM_CORS_ORIGINS="https://app.exemple.com,http://localhost:3000"
# pour autoriser des origines précises avec cookies d'auth (credentials).
cors_origins = os.getenv("HAKIM_CORS_ORIGINS", "")

if not cors_origins:
    # Aucune origine configurée -> on n'autorise que localhost dev (refuse le reste)
    allow_origins_list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    allow_credentials = True
    log.warning(
        "CORS: HAKIM_CORS_ORIGINS non défini — restreint à localhost:3000 (dev). "
        "Configurez HAKIM_CORS_ORIGINS en production."
    )
elif cors_origins == "*":
    # Wildcard explicite demandé : pas de credentials (conforme à la spec CORS)
    allow_origins_list = ["*"]
    allow_credentials = False
    log.warning("CORS: wildcard '*' activé — credentials désactivés.")
else:
    allow_origins_list = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
    expose_headers=["X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

log.info("CORS configuré: origines=%s, credentials=%s", allow_origins_list, allow_credentials)


AUTH_STRICT_PATHS = {"/auth/login", "/auth/register", "/auth/refresh"}


def _client_identifier_from_request(request: Request) -> ClientIdentifier:
    client_ip = request.client.host if request.client else "127.0.0.1"
    return ClientIdentifier(
        client_id=client_ip,
        ip_address=client_ip,
        # Pas de user-agent dans la clé : il est contrôlé par le client et
        # permettrait de contourner la limite en le faisant varier.
    )


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Les requêtes OPTIONS (CORS preflight) ne doivent pas être soumises au rate limit
    if request.method == "OPTIONS":
        return await call_next(request)

    # Limite l'API et les routes d'authentification (/auth, hors /api)
    path = request.url.path
    is_auth_path = path.startswith("/auth/")
    if not (path.startswith("/api/") or is_auth_path):
        return await call_next(request)

    if is_auth_path:
        # Quota strict (anti brute-force) sur login/register/refresh uniquement ;
        # /auth/me, /auth/logout suivent le quota par défaut.
        strict = path in AUTH_STRICT_PATHS
        endpoint_cfg = get_default_rate_limit_for_endpoint("/auth/login" if strict else "/")
        if strict:
            endpoint_cfg.key_prefix = f"auth:{path}"  # un compteur par route
    else:
        endpoint_cfg = get_default_rate_limit_for_endpoint(path)
    cfg = RateLimitConfig(
        max_requests=min(endpoint_cfg.max_requests, RATE_LIMIT_PER_MIN),
        window_seconds=endpoint_cfg.window_seconds,
        burst_size=endpoint_cfg.burst_size,
        penalty_interval=endpoint_cfg.penalty_interval,
        key_prefix=endpoint_cfg.key_prefix,
    )

    client_id = _client_identifier_from_request(request)
    is_allowed, metadata = rate_limiter.is_allowed(client_id, custom_config=cfg)

    if not is_allowed:
        retry_after = max(1, int(metadata.get("reset_time", 60) - time.time()))
        return JSONResponse(
            status_code=429,
            content={"detail": "Trop de requêtes. Veuillez patienter avant d'essayer à nouveau (Rate limit dépassé)."},
            headers={"Retry-After": str(retry_after)},
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(metadata.get("remaining_requests", 0))
    return response

app.include_router(router)
app.include_router(auth_router)
app.include_router(convo_router)


@app.get("/")
async def root():
    return {
        "agent": "APEX v4.0",
        "message": "Orchestrateur multi-agents prêt",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


def start():
    uvicorn.run("axiom.api.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()

