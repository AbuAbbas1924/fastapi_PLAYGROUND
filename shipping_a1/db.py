from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from shipping_a1.main import Redis


class DataBaseSettings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    REDIS_HOST: str
    REDIS_PORT: int
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_file_encoding="utf-8",
        env_ignore_extra=True,
        extra="ignore",
    )

    @property
    def POSTGRES_URL(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = DataBaseSettings()
# print(settings.POSTGRES_URL)

token_blacklist = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


async def add_jti_to_blocklist(jti: str):
    await token_blacklist.set(jti, "blacklisted")


async def check_jti(jti: str):
    return await token_blacklist.exists(jti)


engine = create_async_engine(url=settings.POSTGRES_URL, echo=True)
shipping_a1_meta = MetaData()


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(shipping_a1_meta.create_all)


async def get_session() -> AsyncSession:
    session = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session() as s:
        yield s


sessionDep = Annotated[AsyncSession, Depends(get_session)]
