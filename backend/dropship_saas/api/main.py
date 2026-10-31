"""Main FastAPI application setup for dropship-saas."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


log = __import__('logging').getLogger('dropship_saas.api')


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info('Dropship SaaS API starting')
    yield
    log.info('Dropship SaaS API shutting down')


app = FastAPI(title='Dropship SaaS API', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Import routers here to avoid circular imports
from dropship_saas.api.products import router as products_router
from dropship_saas.api.scraping import router as scraping_router
from dropship_saas.api.monitoring import router as monitoring_router

app.include_router(products_router)
app.include_router(scraping_router)
app.include_router(monitoring_router)


@app.get('/health')
async def health_check():
    return {'status': 'ok', 'service': 'dropship-saas'}


@app.get('/')
async def root():
    return {'message': 'Dropship SaaS API - MVP'}
