import logging

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import MetaData
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)


# *Settings
class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="book_a1/.env", env_file_encoding="utf-8", extra="ignore"
    )
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str


settings = PostgresSettings()

book_a1_meta = MetaData()

class Database:
    def __init__(self, url: str):
        self.async_engine = create_async_engine(settings.DATABASE_URL, echo=True)
        self.async_session = async_sessionmaker(
            self.async_engine, expire_on_commit=False, class_=AsyncSession
        )

    async def __call__(self):
        async with self.async_session() as session:
            yield session

    async def init(self):
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(book_a1_meta.create_all, checkfirst=True)
            logger.info("✓ Database connected successfully")
        except (OperationalError, OSError, ConnectionRefusedError) as e:
            logger.error("✗ Failed to connect to PostgreSQL database")
            logger.error(f"  Error: {str(e)}")
            logger.error(f"  Database URL: {settings.DATABASE_URL}")
            logger.error("  Please ensure PostgreSQL is running and accessible")
            raise RuntimeError(
                "Database connection failed. Please start PostgreSQL and try again."
            ) from e

    async def close(self):
        await self.async_engine.dispose()


db = Database(settings.DATABASE_URL)
