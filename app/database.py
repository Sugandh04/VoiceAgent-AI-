import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, inspect
from app.config import settings

logger = logging.getLogger("database")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    """
    Standard transactional session dependency.
    Does NOT auto-commit on reads. Mutating endpoints commit explicitly.
    Rolls back automatically on unhandled exceptions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """
    Idempotent schema initialization.
    Creates missing tables and performs safe, dialect-aware column checks
    for development environments without masking database errors.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Dialect-aware check for SQLite dev databases
        if "sqlite" in settings.DATABASE_URL:
            cursor = await conn.execute(text("PRAGMA table_info(calls);"))
            existing_cols = {row[1] for row in cursor.fetchall()}

            if "summary" not in existing_cols:
                logger.info("Migrating schema: adding 'summary' column to 'calls' table")
                await conn.execute(text("ALTER TABLE calls ADD COLUMN summary TEXT;"))

            if "to_number" not in existing_cols:
                logger.info("Migrating schema: adding 'to_number' column to 'calls' table")
                await conn.execute(text("ALTER TABLE calls ADD COLUMN to_number VARCHAR(50);"))
