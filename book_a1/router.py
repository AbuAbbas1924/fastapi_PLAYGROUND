import uuid
from datetime import datetime, timezone
from typing import Annotated

import sqlalchemy.dialects.postgresql as pg
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Column, Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from book_a1.postgres import db


class Book(SQLModel, table=True):
    __tablename__ = "books"
    __table__args = {"extend_existing": True}
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        default_factory=uuid.uuid4,
    )
    title: str
    author: str
    publisher: str
    published_data: str
    page_count: int
    language: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    update_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"book-(uid={self.uid}, title={self.title}, author={self.author})"


class BookCreateModel(BaseModel):
    title: str | None = None
    author: str | None = None
    publisher: str | None = None
    published_date: str | None = None
    page_count: str | None = None
    language: str | None = None


# * 2. services


class BookService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, book: Book):
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def create_book(self, book_data: BookCreateModel):
        data_dict = book_data.model_dump(exclude_unset=True)
        book = Book(**data_dict)
        return await self.save(book)

    async def get_books(self):
        result = await self.session.execute(select(Book).order_by(Book.created_at))
        return result.scalars().all()


router = APIRouter(prefix="/book_a1", tags=["book_a1"])
session_dep = Annotated[AsyncSession, Depends(db)]


@router.get("/")
async def get_books(session: session_dep):
    service = BookService(session=session)
    return await service.get_books()


@router.post("/")
async def create_book(book_data: BookCreateModel, session: session_dep):
    service = BookService(session)
    return await service.create_book(book_data)