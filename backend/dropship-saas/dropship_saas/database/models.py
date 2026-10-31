"""Database models for dropship-saas."""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime
import enum

Base = declarative_base()

class SupplierStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ALERT = "alert"
    BLACKLISTED = "blacklisted"

class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    PAUSED = "paused"


class Supplier(Base):
    """Supplier platform (AliExpress, Amazon.fr, etc.)"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    base_url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    health_status = Column(String(50), default="healthy")  # healthy/alert/blacklisted
    last_check_at = Column(DateTime, nullable=True)
    consecutive_empty = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = relationship("Product", back_populates="supplier")


class Product(Base):
    """Product extracted from a supplier."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    source_id = Column(String(200), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    base_title = Column(String(500), nullable=False)
    description = Column(Text)
    currency = Column(String(3), default="EUR")
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    delivery_estimates = relationship("DeliveryEstimate", back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base):
    """Variant of a product (size, color, etc.)"""
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku_source = Column(String(200), nullable=False)
    attributes = Column(JSON, default=dict)  # {"color": "Noir", "size": "XL"}
    cost_price = Column(Float, nullable=False)
    in_stock = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="variants")
    price_history = relationship("PriceHistory", back_populates="variant", cascade="all, delete-orphan")


class PriceHistory(Base):
    """Historical price tracking (TimescaleDB hypertable)."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="EUR")
    recorded_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_history")
    variant = relationship("ProductVariant", back_populates="price_history")

    __table_args__ = (
        # TimescaleDB: this table becomes a hypertable via migration
    )


class DeliveryEstimate(Base):
    """Shipping cost and estimated delivery time."""
    __tablename__ = "delivery_estimates"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    cost = Column(Float, nullable=False)
    min_days = Column(Integer, nullable=False)
    max_days = Column(Integer, nullable=False)

    product = relationship("Product", back_populates="delivery_estimates")


class ScrapingJob(Base):
    """Async scraping job tracking."""
    __tablename__ = "scraping_jobs"

    id = Column(String(100), primary_key=True)
    url = Column(String(1000), nullable=False)
    source_platform = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    payload = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class PricingRule(Base):
    """Automated pricing rules per supplier/shop."""
    __tablename__ = "pricing_rules"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    rule_type = Column(String(20), nullable=False)  # fixed_margin/percent_margin
    margin_value = Column(Float, nullable=False)
    fixed_value = Column(Float, default=0.0)
    round_to_99 = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db(engine):
    """Initialize database and create all tables + TimescaleDB hypertables."""
    Base.metadata.create_all(bind=engine)
    try:
        with engine.connect() as conn:
            # Create TimescaleDB hypertable for price_history
            conn.execute("SELECT create_hypertable('price_history', 'recorded_at')")
            conn.commit()
    except Exception:
        # TimescaleDB extension not available; use standard index fallback
        pass


def make_hypertable(engine, table_name: str, time_column: str):
    """Convert a table to a TimescaleDB hypertable."""
    with engine.connect() as conn:
        conn.execute(
            f"SELECT create_hypertable('{table_name}', '{time_column}')"
        )
        conn.commit()