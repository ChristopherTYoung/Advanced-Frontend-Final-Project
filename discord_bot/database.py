"""Database configuration and session management."""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Database connection settings
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://discord_bot:discord_bot_password@db:5432/discord_bot_db"
)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Create async session factory
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for getting database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (if using SQLAlchemy models)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
