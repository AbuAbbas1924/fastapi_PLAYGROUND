from fastapi import APIRouter, Path
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field

from todo_a1.auth import auth_dependency
from todo_a1.db import Todos, db_dependency

router = APIRouter()


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


@router.post("/todo", status_code=201)
async def create_todo(
    db: db_dependency,
    todo_request: TodoRequest,
    auth: auth_dependency,
):
    todo_model = Todos(**todo_request.model_dump())
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    # return todo_model
    return db.query(Todos).all()


@router.get("/")
async def read_all(db: db_dependency, auth: auth_dependency):
    return db.query(Todos).all()


@router.get("/task/{id}", status_code=200)
async def get_single_task(
    db: db_dependency,
    auth: auth_dependency,
    id: int = Path(gt=0),
):
    # return db.query(Todos).filter(Todos.id == id).first()
    # todo_model = db.query(Todos).filter(Todos.id == id).first()
    # if todo_model is not None:
    #     return todo_model
    # raise HTTPException(status_code=404, detail="Todo not found.")
    if auth is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    todo_model = (
        db.query(Todos)
        .filter(Todos.id == id)
        .filter(Todos.owner_id == auth.get("id"))
        .first()
    )


@router.put("/todo/{id}", status_code=204)
async def update_todo(
    db: db_dependency,
    todo_request: TodoRequest,
    auth: auth_dependency,
    id: int = Path(gt=0),
):
    if auth is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    todo_model = (
        db.query(Todos)
        .filter(Todos.id == id)
        .filter(Todos.owner_id == auth.get("id"))
        .first()
    )
    # todo_model = db.query(Todos).filter(Todos.id == id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found.")

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    # return db.query(Todos).all
    # return todo_model
    return db.query(Todos).filter(Todos.owner_id == auth.get("id")).first()


@router.delete("/todo/{id}", status_code=204)
async def delete_todo(db: db_dependency, auth: auth_dependency, id: int = Path(gt=0)):
    if auth is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    todo_model = (
        db.query(Todos)
        .filter(Todos.id == id)
        .filter(Todos.id == auth.get("id"))
        .first()
    )
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found.")
    # db.query(Todos).filter(Todos.id == id).delete()
    db.query(Todos).filter(Todos.id == id).filter(Todos.id == auth.get("id")).delete()
    db.commit()
    # return db.query(Todos).all()
    return db.query(Todos).all()
