import datetime
from enum import Enum
from random import randint
from typing import Annotated, ClassVar, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# from pydantic import BaseModel
from sqlalchemy import MetaData
from sqlmodel import Field, SQLModel, select

from shipping_a1.db import sessionDep, shipping_a1_meta
from shipping_a1.seller import sellerDep


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
    status: ShipmentStatus
    destination: Optional[int]


class UpdateShipment(BaseModel):
    id: int
    content: str
    weight: float
    destination: int
    status: ShipmentStatus


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

def shipment_callback(session: sessionDep):
    return ShipmentService(session)


serviceDep = Annotated[ShipmentService, Depends(shipment_callback)]


@router.post("/add", status_code=201)
async def create_shipment(
    data: CreateShipment, service: serviceDep, seller: sellerDep
) -> Shipment:
    return await service.create(data)


@router.get("/all", status_code=200)
async def get_all(service: serviceDep, seller: sellerDep) -> list[Shipment]:
    return await service.get_all()


@router.get("/{id}", response_model=Shipment, status_code=200)
async def get_id(id: int, service: serviceDep, seller: sellerDep) -> Shipment:
    return await service.get_id(id)


@router.put("/update", status_code=200)
async def update(data: Shipment, service: serviceDep, seller: sellerDep) -> Shipment:
    return await service.update(data.id, data.model_dump(exclude={"id"}))


@router.delete("/delete", status_code=200)
async def delete(id: int, service: serviceDep, seller: sellerDep) -> dict[str, str]:
    return await service.delete(id)
