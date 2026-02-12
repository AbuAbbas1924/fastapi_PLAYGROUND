import uuid
from datetime import datetime
from typing import Annotated

import sqlalchemy.dialects.postgresql as pg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Column, Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from book_a1.auth import access_token_bearer
from book_a1.db import book_a1_meta, db

# 1. authorize JWT token => curl -X GET "http://localhost:8000/books" -H "Authorization: Bearer <JWT>" -H "accept: application/json"


class Book(SQLModel, table=True):
    __tablename__ = "books"
    __table__args = {"extend_existing": True}
    metadata = book_a1_meta
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        default_factory=uuid.uuid4,
    )
    title: str
    author: str
    publisher: str
    published_date: str
    page_count: int
    language: str
    created_at: datetime = Field(default_factory=datetime.now)
    update_at: datetime = Field(default_factory=datetime.now)

    def __repr__(self) -> str:
        return f"book-(uid={self.uid}, title={self.title}, author={self.author})"


class BookCreateModel(BaseModel):
    title: str
    author: str
    publisher: str
    published_date: str
    page_count: int
    language: str

class BookUpdateModel(BaseModel):
    title: str
    author: str
    publisher: str
    published_date: str
    page_count: int
    language: str

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

    async def get_book(self, book_uid: str):
        result = await self.session.execute(select(Book).where(Book.uid == book_uid))
        result = result.scalar_one_or_none()
        return result

    async def update_book(self, book_uid: str, book_data: BookUpdateModel):
        book_to_update = await self.get_book(book_uid)
        if not book_to_update:
            raise HTTPException(status_code=303, detail="book not found")
        data_dict = book_data.model_dump()
        for key, value in data_dict.items():
            setattr(book_to_update, key, value)

        return await self.save(book_to_update)

    async def delete_book(self, book_uid: str):
        book_to_delete = await self.get_book(book_uid)
        if not book_to_delete:
            raise HTTPException(status_code=404, detail="book not found")
        await self.session.delete(book_to_delete)
        await self.session.commit()
        return book_to_delete

router = APIRouter()
session_dep = Annotated[AsyncSession, Depends(db)]
user_dep = Annotated[dict, Depends(access_token_bearer)]

@router.post("/", status_code=201)
async def create_book(book_data: BookCreateModel, session: session_dep, user: user_dep):
    service = BookService(session)
    return await service.create_book(book_data)

@router.get("/", status_code=200)
async def get_books(session: session_dep, user: user_dep):
    service = BookService(session=session)
    return await service.get_books()

@router.get("/{book_uid}", status_code=200)
async def get_book(book_uid: str, session: session_dep, user: user_dep):
    service = BookService(session=session)
    return await service.get_book(book_uid)


@router.put("/{book_uid}", status_code=204)
async def update_book(
    book_uid: str, book_data: BookUpdateModel, session: session_dep, user: user_dep
):
    service = BookService(session=session)
    return await service.update_book(book_uid, book_data)

@router.delete("/{book_uid}", status_code=202)
async def delete_book(book_uid: str, session: session_dep, user: user_dep):
    service = BookService(session=session)
    return await service.delete_book(book_uid)