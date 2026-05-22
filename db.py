from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings
from models import Base

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent column migrations for schema additions that create_all won't apply
        # to existing tables.
        await conn.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'ru'")
        )
        await conn.execute(
            text("UPDATE users SET language = 'ru' WHERE language IS NULL")
        )


@asynccontextmanager
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
