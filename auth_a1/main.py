import datetime
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Optional

import jwt
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from passlib.context import CryptContext
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio import Redis
from scalar_fastapi import get_scalar_api_reference
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import Field, SQLModel, select

# @ 1. Engine
engine = create_async_engine("sqlite+aiosqlite:///./auth_a1/user.db")
auth_a1_meta = MetaData()

# @asynccontextmanager
# async def lifespan_handler(app: FastAPI):
#     print("INIT ASYNC DB")
#     async with engine.begin() as connection:
#         await connection.run_sync(auth_a1_meta.create_all)
#     yield
#     print("STOPPED ASYNC DB")
#     await engine.dispose()


# ! 2. session

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        finally:
            await session.close()


sessionDependency = Annotated[AsyncSession, Depends(get_session)]


# % 3. models


class Account(SQLModel, table=True):
    metadata = auth_a1_meta
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    password: str


class AccountCreate(BaseModel):
    email: str
    password: str


# * 3.1 settings

# __all__ = ["Redis"]
_base_config = SettingsConfigDict(
    env_file="auth_a1/.env",
    env_ignore_empty=True,
    extra="ignore",
)


class RedisSettings(BaseSettings):
    redis_host: str
    redis_port: int
    redis_db: int

    model_config = _base_config


class SecuritySettings(BaseSettings):
    jwt_secret_key: str
    jwt_algorithm: str
    model_config = _base_config


redis_settings = RedisSettings()
security_settings = SecuritySettings()

_token_blacklist = Redis(
    host=redis_settings.redis_host,
    port=redis_settings.redis_port,
    db=redis_settings.redis_db,
)


async def add_jti(jti: str):
    await _token_blacklist.set(jti, "blacklisted")


async def check_jti(jti: str):
    return await _token_blacklist.exists(jti)


# ^ 3.2 utils
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
# SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_SECRET_KEY = security_settings.jwt_secret_key
JWT_ALGORITHM = security_settings.jwt_algorithm


def encode_token(
    data: dict,
    expires_delta: Optional[datetime.timedelta] = datetime.timedelta(days=10),
):
    expire_time = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    return jwt.encode(
        {
            **data,
            "exp": expire_time,
            "jti": str(uuid.uuid4()),
        },
        key=JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


async def check_token(
    token: Annotated[str, Depends(oauth2_scheme)],  # Should be str, not dict
    session: sessionDependency,
):
    if not token or token.strip() == "":
        raise HTTPException(status_code=401, detail="No token provided")
    decoded_token = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    print("EMAIL", decoded_token.get("email"))
    if decoded_token is None or await check_jti(decoded_token.get("jti")):
        raise HTTPException(
            status_code=401, detail="Token not available or JTI is lost"
        )
    account = await session.execute(
        select(Account).where(Account.email == decoded_token.get("email"))
    )
    return account.scalar_one_or_none()


authorizationDependency = Annotated[Account, Depends(check_token)]


# () 4. services
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AccountService:
    def __init__(self, session: sessionDependency):
        self.session = session

    async def save(self, account: Account):
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def create(self, account: AccountCreate):
        item = Account(
            **account.model_dump(exclude={"password"}, exclude_none=True),
            password=password_context.hash(account.password),
        )
        return await self.save(item)

    async def get_by_email(self, email: str):
        print("----email", email)
        item = await self.session.execute(select(Account).where(Account.email == email))
        return item.scalar_one_or_none()

    async def token(self, email, password):
        # $ get account
        account = await self.get_by_email(email)
        print("account", account)
        pw_check = password_context.verify(password, account.password)  # return bool
        if not account:
            raise HTTPException(status_code=401, detail="Invalid email")
        if not pw_check:
            raise HTTPException(status_code=401, detail="Invalid password")
        return encode_token({"email": account.email})


def service_callback(session: sessionDependency):
    return AccountService(session)


accountDependency = Annotated[AccountService, Depends(service_callback)]

# * 5. API
# router = FastAPI(lifespan=lifespan_handler)
router = APIRouter(tags=["auth_a1"], prefix="/auth_a1")


@router.get("/scalar", include_in_schema=False)
def scalar():
    return get_scalar_api_reference(openapi_url=router.openapi_url, title="FastAPI")


@router.post("/signup", response_model=AccountCreate)
async def signup(account: AccountCreate, service: accountDependency):
    return await service.create(account)


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: accountDependency,
):
    token = await service.token(form_data.username, form_data.password)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/service")
async def auth_with_service(
    user: authorizationDependency,  # This gets the full user account from database
    session: sessionDependency,
):
    return user


@router.get("/logout")
async def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    decoded_token = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    await add_jti(decoded_token.get("jti"))
    return {"message": "Logout successful", "token": decoded_token["jti"]}
