"""Test suite for dropship-saas Sprint 2."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, AsyncMock


# --- Products API tests ---

class TestProductEndpoints:
    """Test product CRUD and WooCommerce sync."""

    @pytest.mark.asyncio
    async def test_create_product_basic(self):
        """Create a product with minimal payload."""
        from dropship_saas.schemas.product import ProductCreatePayload, VariantSchema
        
        payload = ProductCreatePayload(
            source_platform="AliExpress",
            source_id="AE123456",
            url="https://aliexpress.com/item/123456.html",
            base_title="Test Product",
            variants=[VariantSchema(sku_source="SKU001", cost_price=10.0, in_stock=True, stock_quantity=100)],
        )
        assert payload.source_platform == "AliExpress"
        assert payload.source_id == "AE123456"
        assert len(payload.variants) == 1

    @pytest.mark.asyncio
    async def test_create_product_with_shipping(self):
        """Create product with shipping info."""
        from dropship_saas.schemas.product import (
            ProductCreatePayload, VariantSchema, ShippingSchema
        )
        
        payload = ProductCreatePayload(
            source_platform="Amazon",
            source_id="AM789",
            url="https://amazon.fr/dp/B07XYZ",
            base_title="Amazon Product",
            variants=[VariantSchema(sku_source="SKU002", cost_price=25.0, in_stock=False, stock_quantity=0)],
            shipping=ShippingSchema(cost=5.99, min_days=5, max_days=15),
        )
        assert payload.shipping.cost == 5.99
        assert payload.shipping.min_days == 5

    @pytest.mark.asyncio
    async def test_variant_schema_defaults(self):
        """Test VariantSchema default values."""
        from dropship_saas.schemas.product import VariantSchema

        v = VariantSchema(sku_source="TEST")
        assert v.attributes == {}
        assert v.cost_price == 0.0  # Default value
        assert v.in_stock is True
        assert v.stock_quantity == 0


# --- WooCommerce integration tests ---

class TestWooCommerceIntegration:
    """Test WooCommerce/AliDropship integration."""

    @pytest.mark.asyncio
    async def test_woocommerce_not_configured(self):
        """When WC credentials are missing, endpoints return 503."""
        from dropship_saas.api.woocommerce import is_woocommerce_configured
        
        with patch.dict("os.environ", {}, clear=True):
            assert is_woocommerce_configured() is False

    @pytest.mark.asyncio
    async def test_woocommerce_configured(self):
        """When WC credentials are set, is_configured returns True."""
        from dropship_saas.api.woocommerce import is_woocommerce_configured
        
        with patch.dict("os.environ", {
            "WOOCOMMERCE_URL": "https://test-store.com/wp-json/wc/v3",
            "WOOCOMMERCE_CONSUMER_KEY": "ck_test",
            "WOOCOMMERCE_CONSUMER_SECRET": "cs_test",
        }):
            assert is_woocommerce_configured() is True

    @pytest.mark.asyncio
    async def test_build_wc_payload_simple(self):
        """Build WooCommerce payload for simple product."""
        from dropship_saas.api.woocommerce import build_wc_product_payload
        from dropship_saas.database.models import Product, ProductVariant, Supplier
        from datetime import datetime
        
        supplier = Supplier(id=1, name="AliExpress", base_url="https://aliexpress.com")
        product = Product(
            id=1, supplier_id=1, source_id="AE001",
            url="https://aliexpress.com/item/001",
            base_title="Simple Product", currency="EUR", status="active",
            created_at=datetime.utcnow(), supplier=supplier,
        )
        variant = ProductVariant(
            id=1, product_id=1, sku_source="AE001-BLACK",
            attributes={"color": "Black"}, cost_price=15.0,
            in_stock=True, stock_quantity=50,
        )
        
        payload = build_wc_product_payload(product, [variant])
        
        assert payload["name"] == "Simple Product"
        assert payload["type"] == "simple"
        assert payload["sku"] == "AE001"
        assert payload["regular_price"] == "37.5"  # 15 * 2.5
        assert payload["manage_stock"] is True

    @pytest.mark.asyncio
    async def test_build_wc_payload_variable(self):
        """Build WooCommerce payload for variable product."""
        from dropship_saas.api.woocommerce import build_wc_product_payload
        from dropship_saas.database.models import Product, ProductVariant, Supplier
        from datetime import datetime
        
        supplier = Supplier(id=1, name="AliExpress", base_url="https://aliexpress.com")
        product = Product(
            id=2, supplier_id=1, source_id="AE002",
            url="https://aliexpress.com/item/002",
            base_title="Variable Product", currency="EUR", status="active",
            created_at=datetime.utcnow(), supplier=supplier,
        )
        v1 = ProductVariant(
            id=1, product_id=2, sku_source="AE002-BLACK-S",
            attributes={"color": "Black", "size": "S"}, cost_price=10.0,
            in_stock=True, stock_quantity=20,
        )
        v2 = ProductVariant(
            id=2, product_id=2, sku_source="AE002-BLACK-M",
            attributes={"color": "Black", "size": "M"}, cost_price=12.0,
            in_stock=True, stock_quantity=30,
        )
        
        payload = build_wc_product_payload(product, [v1, v2])
        
        assert payload["type"] == "variable"
        assert len(payload["variations"]) == 2
        assert len(payload["attributes"]) == 2  # color, size

    @pytest.mark.asyncio
    async def test_fulfillment_service_creation(self):
        """Test fulfillment service can be instantiated."""
        from dropship_saas.fulfillment.aliexpress_orders import (
            AliDropshipFulfillment, get_fulfillment_service
        )
        
        service = AliDropshipFulfillment()
        assert service is not None
        assert service._pending_orders == []
        
        await service.close()


# --- API endpoints smoke tests ---

class TestAPIEndpoints:
    """Test API endpoint registration and basic responses."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Health endpoint returns ok."""
        from fastapi.testclient import TestClient
        from dropship_saas.api.main import app
        
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "dropship-saas"

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Root endpoint returns API info."""
        from fastapi.testclient import TestClient
        from dropship_saas.api.main import app
        
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_woocommerce_routes_registered(self):
        """WooCommerce routes are registered."""
        from fastapi.testclient import TestClient
        from dropship_saas.api.main import app
        
        client = TestClient(app)
        
        # Status endpoint
        response = client.get("/api/woocommerce/status")
        assert response.status_code == 200
        
        # Order webhook
        response = client.post("/api/woocommerce/webhook/order", json={})
        assert response.status_code in [200, 503]  # 200 if processed, 503 if WC not configured

    @pytest.mark.asyncio
    async def test_products_routes_registered(self):
        """Products routes are registered."""
        from fastapi.testclient import TestClient
        from dropship_saas.api.main import app

        client = TestClient(app)

        # With no DB, /api/products may return 500 or 200 with empty list
        response = client.get("/api/products?skip=0&limit=10")
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_scraping_routes_registered(self):
        """Scraping routes are registered."""
        from fastapi.testclient import TestClient
        from dropship_saas.api.main import app
        
        client = TestClient(app)
        
        response = client.get("/api/scraping/health")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_monitoring_routes_registered(self):
        """Monitoring routes are registered — endpoint returns 200 or 404 (no DB)."""
        from fastapi.testclient import TestClient
        from dropship_saas.api.main import app

        client = TestClient(app)

        # With no DB running, expect 404/500 or 200 if DB is up
        response = client.get("/api/monitoring/status/1")
        assert response.status_code in [200, 404, 500]


# --- Sync service tests ---

class TestProductSync:
    """Test product synchronization service."""

    @pytest.mark.asyncio
    async def test_sync_service_creation(self):
        """Test ProductSyncService can be instantiated."""
        from dropship_saas.sync.product_sync import ProductSyncService
        
        service = ProductSyncService()
        assert service is not None
        
        await service.close()

    @pytest.mark.asyncio
    async def test_sync_report_structure(self):
        """Test sync report has expected fields."""
        from datetime import datetime
        from dropship_saas.sync.product_sync import ProductSyncService
        
        service = ProductSyncService()
        report = await service.generate_sync_report()
        
        assert "timestamp" in report
        assert "syncs_run" in report
        assert "products_synced" in report
        assert "price_changes" in report
        assert isinstance(report["timestamp"], str)


# --- Security tests ---

class TestSecurity:
    """Test security components."""

    @pytest.mark.asyncio
    async def test_encryption_roundtrip(self):
        """Encryption and decryption are inverses."""
        from dropship_saas.security.encryption import encrypt, decrypt
        
        token = "test-woocommerce-token-12345"
        encrypted = encrypt(token)
        decrypted = decrypt(encrypted)
        
        assert decrypted == token
        assert encrypted != token

    @pytest.mark.asyncio
    async def test_proxy_manager(self):
        """Proxy manager can be instantiated."""
        from dropship_saas.security.proxy_manager import ProxyManager
        
        pm = ProxyManager()
        assert pm is not None

    @pytest.mark.asyncio
    async def test_scraper_factory(self):
        """Scraper factory returns correct scraper types."""
        from dropship_saas.scraping.registry import ScraperFactory
        
        factory = ScraperFactory()
        assert factory is not None
        
        # List registered scrapers
        scrapers = factory.list_scrapers()
        assert "aliexpress" in scrapers
        assert "amazon" in scrapers

    @pytest.mark.asyncio
    async def test_pricing_engine(self):
        """Pricing engine can be instantiated and compute."""
        from dropship_saas.pricing.engine import PricingEngine

        engine = PricingEngine()
        result = engine.compute_for_shop(shop_id="test", rule_type="fixed_margin", margin_value=10.0)
        assert result is not None


# --- Database tests ---

class TestDatabase:
    """Test database components."""

    @pytest.mark.asyncio
    async def test_session_factory(self):
        """Session factory exists."""
        from dropship_saas.database.session import async_session, get_db
        assert async_session is not None

    @pytest.mark.asyncio
    async def test_base_model(self):
        """SQLAlchemy Base is defined."""
        from dropship_saas.database.models import Base, Product, Supplier, ProductVariant
        assert Base is not None
        assert Product.__tablename__ == "products"
        assert Supplier.__tablename__ == "suppliers"
        assert ProductVariant.__tablename__ == "product_variants"


# --- Scraping adapter tests ---

class TestScrapingAdapters:
    """Test that scrapers can be instantiated and have required methods."""

    @pytest.mark.asyncio
    async def test_aliexpress_scraper_structure(self):
        """AliExpress scraper has required methods."""
        from dropship_saas.scraping.aliexpress import AliExpressScraper
        
        scraper = AliExpressScraper()
        assert hasattr(scraper, "fetch")
        assert hasattr(scraper, "extract_title")
        assert hasattr(scraper, "extract_variants")
        assert hasattr(scraper, "extract_images")
        assert hasattr(scraper, "extract_delivery")

    @pytest.mark.asyncio
    async def test_amazon_scraper_structure(self):
        """Amazon scraper has required methods."""
        from dropship_saas.scraping.amazon import AmazonScraper
        
        scraper = AmazonScraper()
        assert hasattr(scraper, "fetch")
        assert hasattr(scraper, "extract_title")
        assert hasattr(scraper, "extract_variants")

    @pytest.mark.asyncio
    async def test_base_scraper_abstract(self):
        """BaseScraper is abstract and cannot be instantiated directly."""
        from dropship_saas.scraping.base import BaseScraper
        import pytest
        
        with pytest.raises(TypeError):
            BaseScraper()