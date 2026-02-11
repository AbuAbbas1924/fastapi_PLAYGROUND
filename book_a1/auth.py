import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

# import bcrypt
import jwt
import sqlalchemy.dialects.postgresql as pg
from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlmodel import Column, Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from book_a1.db import db, settings

session_dep = Annotated[AsyncSession, Depends(db)]
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# def generate_password_hash(password: str) -> str:
#     return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def generate_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
    return pwd_context.verify(plain_pwd, hashed_pwd)


ACCESS_TOKEN_EXPIRE = 5


def create_access_token(
    # data: dict, secret_key: str, algorithm: str, expires_delta: int
    data: dict,
    expiry: timedelta = None,
    refresh: bool = False,
):
    # to_encode = data.copy()
    # expire = datetime.utcnow() + expires_delta
    # to_encode.update({"exp": expire})
    # encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    # return encoded_jwt
    payload = {}
    payload["user"] = data
    payload["exp"] = datetime.now(timezone.utc) + (
        expiry if expiry else timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    )
    payload["jti"] = str(uuid.uuid4())
    payload["refresh"] = refresh
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Token invalid")


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    uuid: uuid.UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        default_factory=uuid.uuid4,
    )
    username: str
    email: str
    password: str
    first_name: str | None = None
    last_name: str | None = None
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(pg.TIMESTAMP(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(pg.TIMESTAMP(timezone=True)),
    )

    def __repr__(self) -> str:
        return f"User-(uuid={self.uuid}, username={self.username}, email={self.email})"


class UserCreateModel(SQLModel):
    username: str
    email: str
    password: str


class UserLoginModel(SQLModel):
    email: str
    password: str


class UserService:
    def __init__(self, session: session_dep):
        self.session = session

    async def get_user_by_username(self, username: str):
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str):
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def user_exists(self, email) -> bool:
        user = await self.get_user_by_email(email)
        # return True if user is not None else False
        return True if user else False

    async def save_user(self, user: User):
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_user(self, user_create: UserCreateModel):
        hashed_password = generate_password_hash(user_create.password)
        user = User(
            username=user_create.username,
            email=user_create.email,
            password=hashed_password,
        )
        return await self.save_user(user)

    async def verify_user_credentials(self, user_login: UserLoginModel) -> User | None:
        user = await self.get_user_by_email(user_login.email)
        if user and verify_password(user_login.password, user.password):
            return user
        return None


router = APIRouter()


@router.post("/register", response_model=User, status_code=201)
async def register(user_create: UserCreateModel, session: session_dep):
    user_service = UserService(session)
    user_exists = await user_service.user_exists(user_create.email)
    if user_exists:
        raise HTTPException(status_code=409, detail="user already exists")
    return await user_service.create_user(user_create)


@router.post("/login")
async def login(user_login: UserLoginModel, session: session_dep):
    user_service = UserService(session)
    user = await user_service.verify_user_credentials(user_login)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # access_token = create_access_token({"sub": user.email})
    access_token = create_access_token(
        data={"email": user.email, "username": user.username, "uid": str(user.uuid)}
    )
    refresh_token = create_access_token(
        data={"email": user.email, "username": user.username, "uid": str(user.uuid)},
        expiry=timedelta(minutes=ACCESS_TOKEN_EXPIRE),
        refresh=True,
    )
    return {
        "access_token": access_token,
        "refresh": refresh_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "username": user.username,
            "uid": str(user.uuid),
        },
    }


@router.post("/login2")
async def login2(login_data: UserLoginModel, session: session_dep):
    email = login_data.email
    password = login_data.password
    user = await UserService(session).get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(
        data={"email": user.email, "username": user.username, "uid": str(user.uuid)}
    )
    refresh_token = create_access_token(
        data={"email": user.email, "username": user.username, "uid": str(user.uuid)},
        expiry=timedelta(minutes=ACCESS_TOKEN_EXPIRE),
        refresh=True,
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "user": user}
