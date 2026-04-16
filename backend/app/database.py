from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_optimizer"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()
