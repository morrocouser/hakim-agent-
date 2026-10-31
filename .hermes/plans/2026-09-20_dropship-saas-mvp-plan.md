# Plateforme SaaS Dropshipping — MVP Sprint 1–2 Implementation Plan

> **For Hermes:** Use `delegate_task` (subagent-driven-development) to implement this plan task-by-task. Fresh subagent per task with two-stage review (spec compliance then code quality).

**Goal:** Build a SaaS platform for automating e-commerce dropshipping product extraction, using Scrapling + Hermes Agent as the scraping orchestration layer, and FastAPI + PostgreSQL as the core API/DB.

**Architecture:** Scrapling workers scrape supplier sites (AliExpress, Amazon FR) and return structured JSON payloads → FastAPI API validates with Pydantic and persists to PostgreSQL → Celery workers handle periodic monitoring (price/stock checks). Hermes Agent orchestrates extractions via a dedicated `sources-dropshipping` skill.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, PostgreSQL + TimescaleDB, Celery + Redis, Scrapling, Hermes Agent, Next.js 16 + React 19 + TailwindCSS (Sprint 3+).

---

## Global Constraints

- Target directory: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/` (new module inside existing hakimagent backend, NOT replacing axiom)
- Follow existing project conventions: `.venv`, `pyproject.toml`, `middleware/` rate limiting, JWT auth pattern from `axiom/api/auth_routes.py`
- All endpoints protected by JWT httpOnly cookie auth (existing pattern)
- No shell=True anywhere, binary allowlist for any subprocess calls
- AES-256 encryption for any stored API tokens (Shopify/WooCommerce)
- Scrapling uses adaptive stealth mode with TLS fingerprint emulation
- Rate limit: 2–8 second random delay between scraping requests per supplier
- Health check: if 10 consecutive requests on a source return empty fields → switch worker to alert mode
- Proxy quarantine: disconnect any proxy returning HTTP 403/429 or blocking captcha
- Must be deployable on Windows via WSL2 per spec

---

## Sprint 1: Moteur Scrapling Core (Sprints 1–2 merged for MVP)

### Task 1: Project Scaffold & Dependencies

**Objective:** Create the dropship-saas Python package with all required dependencies and project structure.

**Files:**
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/pyproject.toml`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/.env.example`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/__init__.py`
- Create directory: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/`

**Steps:**
1. Create directory structure
2. Write `pyproject.toml` with: fastapi, uvicorn, pydantic, scrapling, celery, redis, psycopg2-binary, timescaledb, python-dotenv, pydantic-settings
3. Write `.env.example` with: DATABASE_URL, REDIS_URL, SCRAPING_DELAY_MIN, SCRAPING_DELAY_MAX, SUPPLIER_HEALTH_THRESHOLD, PROXY_BLACKLIST_TIMEOUT
4. Verify: `python3 -m py_compile dropship-saas/*.py` — PY_COMPILE_OK

---

### Task 2: Database Models (PostgreSQL + TimescaleDB)

**Objective:** Define SQLAlchemy models for products, variants, suppliers, price history, and monitoring schedules.

**Files:**
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/database/models.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/database/__init__.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/database/session.py`

**Steps:**
1. Define models with SQLAlchemy 2.0 style:
   - `Supplier` (id, name, base_url, is_active, health_status, last_check_at)
   - `Product` (id, supplier_id, source_id, url, title, description, currency, created_at, updated_at) — FK→Supplier
   - `ProductVariant` (id, product_id, sku_source, attributes, cost_price, in_stock, stock_quantity, created_at) — FK→Product
   - `PriceHistory` (id, product_id, variant_id, price, currency, recorded_at) — FK→Product, TimescaleDB hypertable
   - `ScrapingJob` (id, url, status, payload, error, started_at, completed_at)
   - `DeliveryEstimate` (id, product_id, cost, min_days, max_days)
2. Create TimescaleDB hypertable for PriceHistory via `make_hypertable()` migration
3. Create session.py with `get_db()` dependency for FastAPI
4. Verify: `python3 -m py_compile dropship-saas/database/*.py` — PY_COMPILE_OK

---

### Task 3: Pydantic Schemas (Request/Response Validation)

**Objective:** Create Pydantic v2 schemas for all API payloads matching the spec's JSON payload structure.

**Files:**
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/schemas/__init__.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/schemas/product.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/schemas/scraping.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/schemas/monitoring.py`

**Steps:**
1. Product schema: base_title, description, currency (default EUR), variants (list), images (list of URLs), shipping (nested)
2. Scraping payload schema (matches spec 4.2):
   ```python
   {
     "source_platform": "aliexpress",
     "source_id": "1005006283921",
     "url": "https://...",
     "currency": "EUR",
     "base_title": "...",
     "variants": [{"sku_source": "VAR-01", "attributes": {"color": "Noir"}, "cost_price": 14.50, "in_stock": True, "stock_quantity": 42}],
     "shipping": {"cost": 2.99, "min_days": 7, "max_days": 12},
     "images": ["https://..."]
   }
   ```
3. Monitoring schema: schedule_interval, alert_threshold, notification_channel
4. Verify: `python3 -c "from dropship_saas.schemas import product, scraping, monitoring; print('imports ok')"` — imports without error

---

### Task 4: Scrapling Extractors (AliExpress + Amazon.fr)

**Objective:** Implement modular scraper adapters for AliExpress and Amazon.fr using Scrapling stealth mode.

**Files:**
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/scraping/__init__.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/scraping/base.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/scraping/aliexpress.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/scraping/amazon.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/scraping/registry.py`

**Steps:**
1. **base.py** — Abstract `BaseScraper` class:
   - `fetch(product_url: str) -> dict` — abstract method
   - `_get_stealth_fetcher()` — returns Scrapling adaptive fetcher with TLS fingerprint emulation
   - `_apply_rate_limit()` — random delay 2–8 seconds between requests
   - `_extract_images(html)` — parse gallery URLs
   - `_extract_variants(html)` — parse variant structure (size, color, SKU, price, stock)
2. **aliexpress.py** — `AliExpressScraper(BaseScraper)`:
   - Implement `fetch()` for AliExpress product URLs
   - Extract: title, description, specs, HD image URLs, variants (SKU, attributes, cost_price, stock), shipping cost/days
   - Handle AliExpress-specific DOM structure with Scrapling's adaptive filtering
3. **amazon.py** — `AmazonScraper(BaseScraper)`:
   - Implement `fetch()` for Amazon.fr product URLs
   - Extract same fields as AliExpress, adapted for Amazon DOM
   - Handle Amazon's dynamic content via Scrapling adaptive mode
4. **registry.py** — Factory pattern:
   - `get_scraper(url: str) -> BaseScraper` — returns correct scraper based on URL domain
   - Maps: aliexpress.com → AliExpressScraper, amazon.fr → AmazonScraper
5. Verify: `python3 -c "from dropship_saas.scraping.registry import get_scraper; print(get_scraper('https://www.aliexpress.com/item/1005006283921.html'))"` — returns AliExpressScraper instance

---

### Task 5: Bulk/Store Scraping & Selective Extraction

**Objective:** Implement bulk extraction for categories and seller stores, plus selective extraction with dynamic selectors.

**Files:**
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/scraping/bulk.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/scraping/selectors.py`

**Steps:**
1. **bulk.py** — `BulkScraper`:
   - `scrape_category(category_url: str, max_pages: int = 50) -> list[dict]` — paginates through category listings
   - `scrape_store(seller_url: str) -> list[dict]` — extracts all products from a seller's store
   - Uses Scrapling pagination support with rate limiting
2. **selectors.py** — Dynamic selector engine:
   - `extract_with_fallback(html, selectors: list[dict])` — tries multiple CSS selectors, returns first non-empty result
   - Handles micro-variations in CSS class names between page loads
   - Health check: tracks consecutive empty results, triggers alert after 10 failures
3. Verify: `python3 -c "from dropship_saas.scraping.bulk import BulkScraper; from dropship_saas.scraping.selectors import extract_with_fallback; print('bulk + selectors ok')"` — imports OK

---

### Task 6: FastAPI Core API (Product CRUD + Import Endpoints)

**Objective:** Build the core API endpoints for product import, CRUD, and webhook callbacks from Hermes/Scrapling.

**Files:**
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/api/__init__.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/api/main.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/api/products.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/api/scraping.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/api/monitoring.py`

**Steps:**
1. **main.py** — FastAPI app setup:
   - Lifespan: connect to PostgreSQL, create TimescaleDB hypertables if missing
   - CORS middleware (restrict to Next.js origin)
   - Include routers: `/api/products`, `/api/scraping`, `/api/monitoring`
   - Health check endpoint: `GET /health` → `{"status": "ok", "db": "connected"}`
2. **products.py** — CRUD endpoints:
   - `GET /api/products` — list products with pagination (page, page_size params)
   - `GET /api/products/{product_id}` — get product with variants and price history
   - `POST /api/products` — create product from scraping payload (Pydantic validation)
   - `PUT /api/products/{product_id}` — update product (edit text, photos, pricing)
   - `DELETE /api/products/{product_id}` — soft delete
   - `GET /api/products/{product_id}/variants` — list variants
3. **scraping.py** — Scraping endpoints:
   - `POST /api/scraping/import` — single URL import, triggers Scrapling extraction via Hermes Agent, returns product payload
   - `POST /api/scraping/bulk` — bulk/category import (returns job_id for async)
   - `GET /api/scraping/jobs/{job_id}` — check job status and result
4. **monitoring.py** — Monitoring endpoints:
   - `POST /api/monitoring/schedule` — create monitoring schedule for a product
   - `GET /api/monitoring/status/{product_id}` — current stock/price status
5. Verify: `python3 -c "from dropship_saas.api.main import app; print(list(app.routes))"` — app instantiates, routes listed

---

### Task 7: Pricing Engine (Tarification Automatique)

**Objective:** Implement dynamic pricing rules with margin formulas and commercial rounding.

**Files:**
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/pricing/__init__.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/pricing/engine.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/pricing/rules.py`

**Steps:**
1. **rules.py** — Pricing rule types:
   - `fixed_margin`: Prix Vente = (Prix Achat + Frais Port) + Valeur Fixe
   - `percent_margin`: Prix Vente = (Prix Achat + Frais Port) × (1 + Marge%)
   - `round99`: Arrondi commercial `*.99 €` (floor + 0.99, clamped to min price)
2. **engine.py** — `PricingEngine`:
   - `compute_for_product(product) -> dict` — applies configured rule, returns selling_price, margin_amount, margin_percent
   - `convert_currency(amount, from_curr, to_curr)` — stub for daily exchange rate API (returns same currency for MVP)
   - Rounding: commercial rounding per rule
3. Verify: `python3 -c "from dropship_saas.pricing.engine import PricingEngine; e=PricingEngine(); r=e.compute_for_product(cost_price=14.50, shipping=2.99, rule='percent_margin', margin=0.30); print(r)"` — prints computed price

---

### Task 8: Hermes Agent Integration (Skill + Orchestration)

**Objective:** Create the `sources-dropshipping` skill for Hermes Agent and the HTTP bridge between Hermes and the API.

**Files:**
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/hermes/__init__.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/hermes/skill_sources_dropshipping.md`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/hermes/orchestrator.py`

**Steps:**
1. **skill_sources_dropshipping.md** — Hermes skill document:
   - List of supported sources (AliExpress, Amazon FR initially)
   - Fields to extract per product (title, description, specs, HD images, variants, delivery)
   - Cadence rules: 2–8 second random delay between requests
   - Output format: JSON payload matching spec 4.2 schema
2. **orchestrator.py** — `HermesOrchestrator`:
   - `extract_url(url: str) -> dict` — sends request to Hermes Agent (HTTP local via WSL2), receives JSON payload
   - `extract_category(category_url: str) -> list[dict]` — bulk extraction via Hermes
   - `validate_payload(payload: dict) -> bool` — validates against Pydantic schema before API insertion
   - Error handling: timeout after 60s, retry twice on failure
3. Verify: `python3 -c "from dropship_saas.hermes.orchestrator import HermesOrchestrator; o=HermesOrchestrator(); print('orchestrator ok')"` — instantiates (cannot test actual extraction without Hermes running)

---

### Task 9: Celery Workers (Async Scraping Jobs)

**Objective:** Set up Celery with Redis queue for async scraping and monitoring tasks.

**Files:**
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/tasks/__init__.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/tasks/celery_app.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/tasks/scraping_tasks.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/tasks/monitoring_tasks.py`

**Steps:**
1. **celery_app.py** — Celery configuration:
   - Broker: Redis (REDIS_URL env var)
   - Result backend: Redis
   - Task serialization: JSON
   - Timezone: UTC
2. **scraping_tasks.py**:
   - `scrape_single_product(url: str)` — runs Scrapling extractor, validates payload, inserts into DB
   - `scrape_bulk(category_url: str, max_pages: int)` — iterates pages, scrapes each product, returns job_id
3. **monitoring_tasks.py**:
   - `check_stock(product_id: int)` — re-scrape supplier, compare stock, trigger alert if out of stock
   - `check_price(product_id: int)` — re-scrape, compare price, apply pricing rules, notify if margin exceeded
4. Verify: `python3 -c "from dropship_saas.tasks.celery_app import app as celery_app; print(celery_app.conf.broker_url)"` — broker URL configured

---

### Task 10: Security & Resilience

**Objective:** Implement security layer, proxy management, health checks, and data encryption.

**Files:**
- Modify: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/api/main.py` (add middleware)
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/security/__init__.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/security/encryption.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/security/proxy_manager.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/security/health_check.py`

**Steps:**
1. **encryption.py** — AES-256-GCM encryption/decryption for API tokens (Shopify/WooCommerce):
   - `encrypt(plaintext: str, key: bytes) -> str` (base64-encoded iv:authTag:ciphertext)
   - `decrypt(ciphertext: str, key: bytes) -> str`
2. **proxy_manager.py** — Proxy rotation and blacklisting:
   - `get_active_proxy() -> str` — returns next available residential proxy
   - `blacklist_proxy(proxy_url: str)` — quarantine proxy on 403/429/captcha
   - `is_blacklisted(proxy_url: str) -> bool`
3. **health_check.py** — Supplier health monitoring:
   - `check_supplier_health(supplier_id: int) -> dict` — last 10 requests, if all empty → alert mode
   - `get_health_report() -> dict` — summary of all supplier health statuses
4. Add middleware to API main.py:
   - Rate limiting on scraping endpoints (requests per minute per user)
   - JWT auth via existing pattern (from axiom/api/auth_routes.py)
5. Verify: `python3 -m py_compile dropship-saas/security/*.py` — PY_COMPILE_OK

---

## Sprint 2: Connecteur Shopify (Sprint 3)

### Task 11: Shopify API Integration

**Objective:** Build Shopify REST/GraphQL connector for product sync (MVP integration).

**Files:**
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/integrations/__init__.py`
- Create: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/integrations/shopify.py`
- Modify: `/c/Users/hp/Desktop/hakimagent/backend/dropship-saas/api/products.py` (add sync endpoints)

**Steps:**
1. **shopify.py** — `ShopifyClient`:
   - `authenticate(shop_domain: str, access_token: str)` — store encrypted token
   - `create_product(product_data: dict)` — create product in Shopify with variants
   - `update_product(product_id: str, updates: dict)` — update existing Shopify product
   - `delete_product(product_id: str)` — remove from Shopify
   - `fetch_orders(shop_domain: str)` — retrieve new orders for processing
2. **products.py** modifications:
   - `POST /api/products/{id}/sync-shopify` — push product to Shopify
   - `POST /api/products/bulk-sync-shopify` — sync all products
   - `GET /api/shopify/orders` — fetch orders from connected Shopify
3. Verify: `python3 -c "from dropship_saas.integrations.shopify import ShopifyClient; print('shopify client ok')"` — imports OK

---

## Sprint 3+ (Future): Dashboard, Other Suppliers, Auto-Fulfillment

_Planned but not implemented in this MVP:_
- Next.js dashboard (Sprint 5)
- Cdiscount, Temu, Shein, CJ Dropshipping adapters (roadmap)
- Celery monitoring cron jobs (Sprint 4)
- Auto-fulfillment Phase 2 (automated purchase scripts)

---

## Verification Gate (Complete MVP)

Run these to confirm the MVP works:

1. `python3 -m py_compile backend/dropship-saas/**/*.py` — all Python files compile
2. `python3 -c "from dropship_saas.api.main import app; routes = [r.path for r in app.routes]; assert '/health' in routes; assert '/api/products' in routes; assert '/api/scraping' in routes; assert '/api/monitoring' in routes; print('API routes verified')"`
3. `python3 -c "from dropship_saas.schemas.product import *; from dropship_saas.schemas.scraping import *; from dropship_saas.schemas.monitoring import *; print('Schemas verified')"`
4. `python3 -c "from dropship_saas.scraping.registry import get_scraper; s = get_scraper('https://www.aliexpress.com/item/test.html'); assert hasattr(s, 'fetch'); print('Scraper registry verified')"`
5. `python3 -c "from dropship_saas.pricing.engine import PricingEngine; e = PricingEngine(); r = e.compute_for_product(cost_price=14.50, shipping=2.99, rule='percent_margin', margin=0.30); assert r['selling_price'] == (14.50+2.99)*1.30; print('Pricing engine verified')"`
6. `python3 -c "from dropship_saas.security.encryption import encrypt, decrypt; key = b'0'*32; test = 'test_token'; enc = encrypt(test, key); assert decrypt(enc, key) == test; print('Encryption verified')"`
7. Database migration: PostgreSQL running, TimescaleDB extension installed, `init_db()` creates all tables + PriceHistory hypertable

---

## Risks & Tradeoffs

- **Scrapling depends on browser automation** — if Scrapling cannot run headless in WSL2, fall back to Playwright-based fetching
- **TimescaleDB requires separate extension** — if unavailable, fall back to standard PostgreSQL with `recorded_at` index
- **Hermes Agent HTTP bridge** — local WSL2 networking must allow backend→Hermes communication on localhost
- **Proxy availability** — MVP can run without proxies for testing but production requires residential proxies
- **Scope reduction**: Only AliExpress + Amazon FR for MVP per spec; other suppliers are roadmap items

---

## Plan Date: 2026-09-20
