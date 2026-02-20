import datetime
from enum import Enum
from random import randint
from typing import Annotated, ClassVar

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import MetaData
from sqlmodel import Field, SQLModel, select

from shipping_a1.db import sessionDep, shipping_a1_meta


def random_destination():
    return randint(1000, 9999)


class ShipmentStatus(str, Enum):
    placed = "placed"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    canceled = "canceled"
    unknown = "unknown"


router = APIRouter(prefix="/ship", tags=["ship"])


class BaseShipment(SQLModel):
    metadata: ClassVar[MetaData] = shipping_a1_meta
    content: str
    weight: float = Field(lt=25, gt=0)
    destination: int = Field(default_factory=random_destination)


class Shipment(BaseShipment, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: ShipmentStatus = Field(default=ShipmentStatus.placed)
    estimated_delivery: datetime.datetime = Field(default_factory=datetime.datetime.now)


class ShipmentService:
    def __init__(self, session: sessionDep):
        self.session = session

    async def create(self, data: CreateShipment) -> Shipment:
        shipment = Shipment(
            **data.model_dump(
                exclude={"id", "estimated_delivery", "status"}, exclude_none=True
            ),
            status=ShipmentStatus.placed,
            estimated_delivery=datetime.datetime.now(),
        )
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def get_all(self) -> list[Shipment]:
        items = await self.session.execute(select(Shipment))
        return items.scalars().all()

    async def get_id(self, id: int) -> Shipment:
        # item = await self.session.execute(select(Shipment).where(Shipment.id == id))
        # item = item.scalars().first()
        item = await self.session.get(Shipment, id)
        if item is None:
            raise HTTPException(status_code=404, detail="Shipment not found")
        return item

    async def update(self, id: int, shipment: dict) -> Shipment:
        # item = await self.session.get(Shipment, id)
        item = await self.get_id(id)
        item.sqlmodel_update(shipment)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, id: int) -> None:
        # item = await self.get_id(id)
        # await self.session.delete(item)
        # await self.session.commit()
        await self.session.delete(await self.get_id(id))
        await self.session.commit()
        return {"detail": f"Shipment ID: {id} deleted"}


class CreateShipment(BaseModel):
    content: str
    weight: float
    destination: int


@router.post("/add")
async def create_shipment(data: CreateShipment, session: sessionDep) -> Shipment:
    return await ShipmentService(session).create(data)


@router.get("/all")
async def get_all(session: sessionDep) -> list[Shipment]:
    return await ShipmentService(session).get_all()


@router.get("/{id}", response_model=Shipment)
async def get_id(id: int, session: sessionDep) -> Shipment:
    return await ShipmentService(session).get_id(id)


class UpdateShipment(BaseModel):
    id: int
    content: str
    weight: float
    destination: int
    status: ShipmentStatus


@router.put("/update")
async def update(data: UpdateShipment, session: sessionDep) -> Shipment:
    return await ShipmentService(session).update(data.id, data.model_dump())


@router.delete("/delete")
async def delete(id: int, session: sessionDep) -> dict[str, str]:
    return await ShipmentService(session).delete(id)