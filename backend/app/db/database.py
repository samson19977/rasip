"""
Async SQLAlchemy setup — NeonDB PostgreSQL.
NeonDB uses pooled connections. SSL is required.
asyncpg connection string uses ssl=require (not sslmode).
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    pass


async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",
    # NeonDB pooler: keep pool small
    pool_size=3,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,          # recycle connections every 5 min (NeonDB autosuspend)
    connect_args={"ssl": "require"},   # NeonDB requires SSL
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables on startup (idempotent)."""
    async with async_engine.begin() as conn:
        from app.models import db_models  # noqa — register models
        await conn.run_sync(Base.metadata.create_all)
