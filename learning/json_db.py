import json

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

all_data = {}


@router.get("/")
async def get_all():
    with open("learning/db.json") as json_file:
        data = json.load(json_file)
        for value in data:
            all_data[value["id"]] = value
    return all_data


class TodoModel(BaseModel):
    id: int
    item: str
    complete: bool | None = False


@router.post("/")
async def save_data(todo: TodoModel):
    all_data[todo.id] = todo.model_dump()
    with open("learning/db.json", "w") as json_file:
        json.dump(list(all_data.values()), json_file)
    return todo
