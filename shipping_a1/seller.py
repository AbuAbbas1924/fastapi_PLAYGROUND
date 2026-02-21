from datetime import datetime, timedelta, timezone
from typing import Annotated, ClassVar, Optional
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import MetaData
from sqlmodel import Field, SQLModel, select

from shipping_a1.db import (
    add_jti_to_blocklist,
    check_jti,
    sessionDep,
    settings,
    shipping_a1_meta,
)

pwd_cxt = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_token = OAuth2PasswordBearer(tokenUrl="/shipping_a1/seller/login")


class Seller(SQLModel, table=True):
    metadata: ClassVar[MetaData] = shipping_a1_meta
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    password: str


def generate_access_token(
    data: dict, expires_delta: Optional[timedelta] = timedelta(minutes=30)
):
    # to_encode = data.copy()
    print(f"ENCODE: {data}")
    return jwt.encode(
        payload={
            **data,
            "exp": datetime.now(timezone.utc) + expires_delta,
            "jti": str(uuid4()),
        },
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        return None


decodeTokenDep = Annotated[str, Depends(oauth2_token)]


async def get_access_token(token: decodeTokenDep):
    data = decode_access_token(token)
    if data is None or await check_jti(data.get("jti")):
        raise HTTPException(status_code=401, detail="failed to access token")
    return data


accessTokenDep = Annotated[dict, Depends(get_access_token)]


async def get_current_seller(token: accessTokenDep, session: sessionDep):
    return await session.get(Seller, token["id"])


sellerDep = Annotated[Seller, Depends(get_current_seller)]


class AccessTokenBearer(HTTPBearer):
    async def __call__(self, request):
        auth_credentials = await super().__call__(request)
        print("auth_credentials", auth_credentials)
        token = auth_credentials.credentials
        token_data = decode_access_token(token)
        if token_data is None:
            raise HTTPException(status_code=401, detail="invalid access token")
        return token_data


access_token_bearer = AccessTokenBearer()
tokenBearerDep = Annotated[dict, Depends(access_token_bearer)]
class SellerService:
    def __init__(self, session: sessionDep):
        self.session = session

    async def authenticate(self, email: str, password: str):
        seller = await self.session.execute(select(Seller).where(Seller.email == email))
        seller = seller.scalar_one_or_none()
        if seller is None or not pwd_cxt.verify(password, seller.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = generate_access_token(data={"email": seller.email, "id": seller.id})
        return {"access_token": token, "token_type": "bearer"}

    async def create(self, seller: Seller):
        item = Seller(
            **seller.model_dump(exclude={"password"}, exclude_none=True),
            password=pwd_cxt.hash(seller.password),
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_all(self):
        return await self.session.execute(select(Seller))

    async def get_by_id(self, id: int):
        return await self.session.get(Seller, id)

    async def update(self, id: int, seller: Seller):
        item = await self.get_by_id(id)
        item.sqlmodel_update(seller)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, id: int):
        item = await self.get_by_id(id)
        await self.session.delete(item)
        await self.session.commit()
        return item


def seller_callback(session: sessionDep):
    return SellerService(session)


sellerServiceDep = Annotated[SellerService, Depends(seller_callback)]

router = APIRouter(prefix="/seller", tags=["seller"])


class RegisterModel(BaseModel):
    email: str
    username: str
    password: str


@router.post("/signup")
async def create_seller(seller: RegisterModel, service: sellerServiceDep):
    return await service.create(seller)

# login via email and password
@router.post("/login")
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], service: sellerServiceDep
):
    return await service.authenticate(form.username, form.password)


# curl 127.0.0.1:8000/shipping_a1/seller/dashbaoard -H "Authorization: Bearer TOKEN"
@router.get("/dashboard")
async def dashboard(token: decodeTokenDep, session: sessionDep):
    data = decode_access_token(token)
    # seller = await session.execute(select(Seller).where(Seller.id == data["id"]))
    # seller = seller.scalar_one_or_none()
    seller = await session.get(Seller, data["id"])
    if seller is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"email": seller.email, "username": seller.username}


@router.get("/dashboard2")
# async def dashboard(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/seller/token"))):
async def dashboard2(token: decodeTokenDep):
    return token

@router.get("/logout")
async def logout(token: accessTokenDep):
    await add_jti_to_blocklist(token["jti"])
    return {"msg": "logout", "deleted_token": token}