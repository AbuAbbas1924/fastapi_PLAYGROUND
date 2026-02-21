from typing import Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field
from starlette import status

app = FastAPI()
BOOKS = []


class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int
    published_date: int

    def __init__(self, id, title, author, description, rating, published_date):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
        self.published_date = published_date


class BookRequest(BaseModel):
    id: Optional[int] = Field(description="ID is not needed on create", default=None)
    title: str = Field(min_length=3)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=0, lt=5)
    published_date: int = Field(gt=1999, lt=2031)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "BBB",
                "author": "AAA",
                "description": "DDD",
                "rating": 5,
                "published_date": 2029,
            }
        }
    }


BOOKS = [
    Book(1, "Computer Science Pro", "codingwithroby", "A very nice book!", 5, 2030),
    Book(2, "Be Fast with FastAPI", "codingwithroby", "A great book!", 5, 2030),
    Book(3, "Master Endpoints", "codingwithroby", "A awesome book!", 5, 2029),
    Book(4, "HP1", "Author 1", "Book Description", 2, 2028),
    Book(5, "HP2", "Author 2", "Book Description", 3, 2027),
    Book(6, "HP3", "Author 3", "Book Description", 1, 2026),
]


@app.get("/books", status_code=status.HTTP_200_OK)
async def get_books():
    return BOOKS


# @app.post("/create_book")
# async def create_book(book_request=Body()):
#     BOOKS.append(book_request)
#     return BOOKS


@app.get("/books/{book_id}", status_code=status.HTTP_200_OK)
async def get_book(book_id: int = Path(gt=0)):
    for book in BOOKS:
        if book.id == book_id:
            return book
        else:
            raise HTTPException(status_code=404, detail="ID not found")


@app.get("/rating")
async def get_book_by_rating(book_rating: int = Query(gt=0, lt=6)):
    book_of_return = []
    for book in BOOKS:
        if book.rating == book_rating:
            book_of_return.append(book)
    return book_of_return


@app.get("/books/publish/")
async def filter_by_publish(published_date: int = Query(gt=1999, lt=2031)):
    return [book for book in BOOKS if book.published_date == published_date]


def get_id(book: Book):
    book.id = 1 if len(BOOKS) == 0 else BOOKS[-1].id + 1
    # if len(BOOKS) > 0:
    #     book.id = BOOKS[-1].id + 1
    # else:
    #     book.id = 1
    return book


@app.post("/create_book", status_code=status.HTTP_201_CREATED)
async def create_book_with_model(book_request: BookRequest):
    new_book = Book(**book_request.model_dump())
    BOOKS.append(get_id(new_book))
    return BOOKS


@app.put("/books/update_book", status_code=status.HTTP_204_NO_CONTENT)
async def update_book(book: BookRequest):
    book_changed = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book.id:
            BOOKS[i] = book
            book_changed = True
        if not book_changed:
            HTTPException(status_code=404, detail="not changed")
        return BOOKS[i]


@app.delete("/books/delete/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int):
    book_changed = False
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            BOOKS.pop(i)
            book_changed = True
            break
    if not book_changed:
        HTTPException(status_code=404, detail="not changed")
    return BOOKS
