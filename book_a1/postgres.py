from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


# *Settings
class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="book_a1/.env", env_file_encoding="utf-8", extra="ignore")
    DATABASE_URL: str

postgres_settings = PostgresSettings()

class Database:
    def __init__(self, url:str):
        self.async_engine = create_async_engine(postgres_settings.DATABASE_URL, echo=True)
        self.async_session = async_sessionmaker(self.async_engine, expire_on_commit=False, class_=AsyncSession)

    async def __call__(self):
        async with self.async_session() as session:
            yield session

    async def init(self):
        async with self.async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)

    @asynccontextmanager
    async def async_lifespan(self, app: FastAPI):
        await self.init()
        yield

db = Database(postgres_settings.DATABASE_URL)