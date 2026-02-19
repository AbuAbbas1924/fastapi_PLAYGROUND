from datetime import datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine

engine = create_engine("sqlite:///auth_b1/db.db")


def create_tables():
    return SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


router = APIRouter(tags=["auth_b1"], prefix="/auth_b1")

pwd_context = CryptContext(
    schemes=["argon2"], deprecated="auto", bcrypt__truncate_error=False
)


SECRET_KEY = "ced2f9e33301675072c20a145c3a8ca40fd13b0a2bea2b7172aad7b1e781fba9"
# SECRET_KEY = "a"
ALGORITHM = "HS256"


def hashing_password(password: str) -> str:
    return pwd_context.hash(password)


# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)

# import hashlib
# import base64


# def _prehash(password: str) -> str:
#     return base64.b64encode(hashlib.sha256(password.encode()).digest()).decode()


# def hashing_password(password: str) -> str:
#     return pwd_context.hash(_prehash(password))


class Users(SQLModel, table=True):
    __tablename__ = "auth_b1_users"

    id: int = Field(default=None, primary_key=True, index=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    first_name: str
    last_name: str
    hashed_password: str
    is_active: bool = Field(default=True)
    role: str


create_tables()


@router.get("/auth")
async def get_user():
    return {"message": "auth"}


@router.post("/create_user", response_model=Users)
async def create_user(users: Users, session: Session = Depends(get_session)):
    users.hashed_password = hashing_password(users.hashed_password)
    session.add(users)
    session.commit()
    session.refresh(users)
    return users


def authenticate_user(
    username: str, password: str, session: Session = Depends(get_session)
):
    # user = session.get(Users, username)
    user = session.query(Users).filter(Users.username == username).first()
    print("user", user)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user


def create_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id, "exp": datetime.utcnow() + expires_delta}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/token", response_model=Token)
async def login_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_session),
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Could not validate user.")
    token = create_token(user.username, user.id, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}
