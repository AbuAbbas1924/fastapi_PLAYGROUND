from typing import Annotated, ClassVar, Optional

from fastapi import APIRouter, Depends
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import MetaData
from sqlmodel import Field, SQLModel, select

from shipping_a1.db import sessionDep, shipping_a1_meta

pwd_cxt = CryptContext(schemes=["argon2"], deprecated="auto")


class Seller(SQLModel, table=True):
    metadata: ClassVar[MetaData] = shipping_a1_meta
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    password: str


class SellerService:
    def __init__(self, session: sessionDep):
        self.session = session

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


def seller_service(session: sessionDep):
    return SellerService(session)


sellerDep = Annotated[SellerService, Depends(seller_service)]

router = APIRouter(prefix="/seller", tags=["seller"])


class RegisterModel(BaseModel):
    email: str
    name: str
    password: str


@router.post("/signup")
async def create_seller(seller: RegisterModel, service: sellerDep):
    return await service.create(seller)
