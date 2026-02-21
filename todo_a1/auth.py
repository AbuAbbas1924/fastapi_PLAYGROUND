from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# import jwt
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from todo_a1.db import Users, db_dependency

SECRET_KEY = "87339bee2ca34b7cb0f194973c37c7cf2718a12be734f14d2d8968a104e96f80"
ALGORITHM = "HS256"

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="todo_a1/auth/login")


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return True


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithm=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=401,
                detail="could not validate user.",
            )
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="could not validate user.")


auth_dependency = Annotated[dict, Depends(get_current_user)]


class Token(BaseModel):
    access_token: str
    token_type: str


class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    password: str


router = APIRouter()
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/")
async def get_user():
    return {"user": "test"}


@router.post("/register", status_code=201)
async def create_user(create_user_request: CreateUserRequest, db: db_dependency):
    create_user_model = Users(
        # **create_user_request.dict()
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        # hashed_password=create_user_request.password,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True,
    )
    db.add(create_user_model)
    db.refresh()
    db.commit()
    return create_user_model


login_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post("/login", response_model=Token)
async def login_token(db: db_dependency, form_data: login_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return "user not exists"
    token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return {"user": user, "token_type": "bearer", "token": token}
