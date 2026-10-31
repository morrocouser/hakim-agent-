"""Database session factory for dropship-saas."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import os
from dropship_saas.database.models import Base

# Build database URL from env; fall back to .env if needed
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://dropship:dropship123@localhost:5432/dropship_saas")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def init_db_sync():
    """Synchronous DB init for startup lifecycle."""
    from dropship_saas.database.models import init_db as _init_db
    _init_db(engine)