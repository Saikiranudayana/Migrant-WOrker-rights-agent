"""
Database connection and session management using SQLAlchemy async.
"""
from __future__ import annotations

from typing import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.APP_DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


async def init_db() -> None:
    """Create all database tables on startup."""
    # Import all models so SQLAlchemy discovers them
    import app.models.conversation  # noqa: F401
    import app.models.message       # noqa: F401
    import app.models.source        # noqa: F401
    import app.models.audit_log     # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
