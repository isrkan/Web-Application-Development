"""
Database Configuration - SQLAlchemy with Async Support

This module sets up the database connection and session management:
- Async SQLAlchemy for non-blocking database operations
- MySQL database with aiomysql async driver
- Session management
- Base class for models
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Database URL
# MySQL with aiomysql driver for async support
# Format: mysql+aiomysql://user:password@host:port/database_name
DATABASE_URL = "mysql+aiomysql://root:mysql1@localhost:3306/products_db"

# Create async engine
# echo=True logs all SQL statements (useful for debugging)
# pool_recycle=3600 prevents MySQL "gone away" errors on idle connections
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True,
    pool_recycle=3600
)

# Create async session factory
# expire_on_commit=False keeps objects usable after commit
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all models
# All model classes will inherit from this
Base = declarative_base()


async def get_session() -> AsyncSession:
    """
    Dependency for getting database sessions

    Yields an async session and ensures it's closed after use.
    Use with FastAPI's Depends():
        async def endpoint(session: AsyncSession = Depends(get_session)):

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize database

    Creates all tables defined in models.
    Call this on application startup.
    """
    async with engine.begin() as conn:
        # Create all tables
        # In production, use Alembic for migrations instead
        await conn.run_sync(Base.metadata.create_all)
