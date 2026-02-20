import datetime
from enum import Enum
from random import randint
from typing import ClassVar

from fastapi import APIRouter, HTTPException
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


class CreateShipment(BaseModel):
    content: str
    weight: float
    destination: int


@router.post("/add")
async def create_shipment(data: CreateShipment, session: sessionDep) -> Shipment:
    # shipment = Shipment(**data.model_dump())
    shipment = Shipment(
        **data.model_dump(
            exclude={"id", "estimated_delivery", "status"}, exclude_none=True
        ),
        status=ShipmentStatus.placed,
        estimated_delivery=datetime.datetime.now(),
    )
    session.add(shipment)
    await session.commit()
    await session.refresh(shipment)
    return shipment


@router.get("/all")
async def get_all(session: sessionDep) -> list[Shipment]:
    items = await session.execute(select(Shipment))
    return items.scalars().all()


@router.get("/{id}", response_model=Shipment)
async def get_id(id: int, session: sessionDep) -> Shipment:
    item = await session.execute(select(Shipment).where(Shipment.id == id))
    item = item.scalars().first()
    if item is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return item

class UpdateShipment(BaseModel):
    id: int
    content: str
    weight: float
    destination: int
    status: ShipmentStatus


@router.put("/update")
async def update(data: UpdateShipment, session: sessionDep) -> Shipment:
    item = await session.get(Shipment, data.id)
    if item is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    item.sqlmodel_update(data.model_dump(exclude={"id"}, exclude_none=True))
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete("/delete")
async def delete(id: int, session: sessionDep) -> dict[str, str]:
    item = await session.get(Shipment, id)
    if item is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    await session.delete(item)
    await session.commit()
    return {"detail": f"Shipment ID: {id} deleted"}