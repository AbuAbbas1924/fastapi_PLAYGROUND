from fastapi import APIRouter, Depends, FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Field, Session, SQLModel, create_engine


class Todo(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    task: str
    priority: int = Field(default=0)
    completed: bool = Field(default=False)


engine = create_engine(
    "sqlite:///./htmx_todo_a1/sqlite.db", connect_args={"check_same_thread": False}
)
SQLModel.metadata.create_all(bind=engine)


def get_session():
    with Session(engine) as session:
        yield session


router = APIRouter(tags=["htmx_todo_a1"], prefix="/htmx_todo_a1")


templates = Jinja2Templates(directory="htmx_todo_a1/templates")

# @router.post("/create", response_model=Todo, status_code=status.HTTP_201_CREATED)
# async def create1(request: Request, session: Session = Depends(get_session)):
#     data = dict(await request.form())
#     data["completed"] = data.get("completed", False)
#     obj = Todo(**data)
#     print("Received new task:", obj)
#     session.add(obj)
#     session.commit()
#     session.refresh(obj)
#     return obj


# @router.post("/create", response_model=Todo, status_code=status.HTTP_201_CREATED)
# async def create2(
#     task: str = Form(...),
#     priority: int = Form(),
#     completed: bool = Form(False),
#     session: Session = Depends(get_session),
# ):
#     print(
#         "Received new task:",
#         {"task": task, "priority": priority, "completed": completed},
#     )
#     obj = Todo(task=task, priority=priority, completed=completed)
#     session.add(obj)
#     session.commit()
#     session.refresh(obj)
#     return obj


# @router.post("/create", response_model=Todo, status_code=status.HTTP_201_CREATED)
# async def create3(todo: Todo, session: Session = Depends(get_session)):
#     print("Received new task:", todo)
#     session.add(todo)
#     session.commit()
#     session.refresh(todo)
#     return todo


@router.post(
    "/create", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED
)
async def create4(request: Request, session: Session = Depends(get_session)):
    try:
        data = await request.json()
    except Exception:
        data = dict(await request.form())
    data["completed"] = data.get("completed", False)
    obj = Todo(**data)
    print("Received new task:", obj)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    # return obj
    # todos = session.query(Todo).all()
    # return templates.TemplateResponse("todo_list.html", {"request": request, "todos": todos})
    todo = session.query(Todo).get(obj.id)
    return templates.TemplateResponse("task.html", {"request": request, "todo": todo})


@router.get("/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def root(request: Request, todo: Todo = Depends(get_session)):
    todos = todo.query(Todo).all()
    return templates.TemplateResponse(
        "index.html", {"request": request, "todos": todos}
    )


# @router.put("/toggle/{todo_id}", response_class=HTMLResponse)
# async def toggle1(
#     request: Request, session: Session = Depends(get_session), todo_id: int = None
# ):
#     print("toggle", todo_id)
#     todo = session.query(Todo).get(todo_id)
#     if not todo:
#         return "div>not found</div>"
#     # if todo.completed:
#     #     todo.completed = False
#     # else:
#     #     todo.completed = True
#     todo.completed = not todo.completed
#     session.add(todo)
#     session.commit()
#     session.refresh(todo)
#     return templates.TemplateResponse("task.html", {"request": request, "todo": todo})


@router.put("/toggle", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def toggle2(request: Request, session: Session = Depends(get_session)):
    try:
        data = await request.json()
    except Exception:
        data = dict(await request.form())
        print("data", data)
    todo_id = int(data.get("id"))
    todo = session.query(Todo).get(todo_id)
    if not todo:
        return "<div>not found</div>"
    todo.completed = not todo.completed
    print("class", todo)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return templates.TemplateResponse("task.html", {"request": request, "todo": todo})


@router.get("/edit/{todo_id}", response_class=HTMLResponse)
async def get_form(
    request: Request, session: Session = Depends(get_session), todo_id: int = None
):
    print("edit", todo_id)
    todo = session.query(Todo).get(todo_id)
    if not todo:
        return "<div>not found</div>"
    return templates.TemplateResponse("edit.html", {"request": request, "todo": todo})


@router.patch(
    "/edit/{todo_id}", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED
)
async def edit(
    request: Request, session: Session = Depends(get_session), todo_id: int = None
):
    print("type:", type(todo_id), "todo_id: ", todo_id)
    try:
        data = await request.json()
    except Exception:
        data = dict(await request.form())
        print("data", data)
    todo = session.query(Todo).get(todo_id)
    print("before", todo)
    todo = Todo(**data)
    print("after", todo)
    if not todo:
        return "<div>not found</div>"
    todo.task = data.get("task")
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return templates.TemplateResponse("task.html", {"request": request, "todo": todo})


@router.delete(
    "/delete/{todo_id}",
    response_class=HTMLResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete(
    request: Request, session: Session = Depends(get_session), todo_id: int = None
):
    print("delete", todo_id)
    todo = session.query(Todo).get(todo_id)
    if not todo:
        return "<div>not found</div>"
    session.delete(todo)
    session.commit()
    return '<div class="text-red-500">deleted</div>'
