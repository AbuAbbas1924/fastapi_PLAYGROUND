from enum import Enum
from random import randint
from typing import Any

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field


def random_destination():
    return randint(1000, 9999)


class ShipmentStatus(str, Enum):
    placed = "placed"
    shipped = "shipped"
    in_transit = "in transit"
    delivered = "delivered"
    returned = "returned"
    processing = "processing"


class Shipment(BaseModel):
    content: str
    weight: float = Field(lt=25, gt=0)
    destination: int | None = Field(default_factory=random_destination)
    status: ShipmentStatus = Field(default=ShipmentStatus.placed)


router = APIRouter(prefix="/tests")


@router.get("/id/{id}")
async def get_id(id: int):
    return {"id": id}


@router.get("/valid")
def valid() -> dict[
    # str, int | float
    str, Any
]:
    return {"key1": 234, "key2": 1.4, "key3": "4", "key4": False}


shipments = {
    1: {"weight": 0.6, "content": "glassware", "status": "placed"},
    2: {"weight": 2.3, "content": "books", "status": "shipped"},
    3: {"weight": 1.1, "content": "electronics", "status": "delivered"},
    4: {"weight": 3.5, "content": "furniture", "status": "in transit"},
    5: {"weight": 0.9, "content": "clothing", "status": "returned"},
    6: {"weight": 4.0, "content": "appliances", "status": "processing"},
    7: {"weight": 1.8, "content": "toys", "status": "placed"},
}


@router.get("/")
async def get_all():
    return shipments


@router.get("/latest")
async def latest():
    id = max(shipments.keys())
    if id not in shipments:
        return {"error": "id doesn't exist"}
    return {"content": shipments[id]}


@router.get("/ship_id", response_model=Shipment)
def ship_id(id: int | None = None) -> dict[str, Any]:
    if not id:
        id = max(shipments.keys())
        return shipments[id]
        print("test")
    if id not in shipments:
        return {"detail": "Given id doesn't exist!"}
        raise HTTPException(status_code=404, detail="Given id doesn't exist!")
        # return {"detail": "Given id doesn't exist!"}
    # return {"content": shipments[id]}
    return shipments[id]


@router.post("/create_ship")
# async def create(content: str, weight: float) -> dict[str, int]:
# async def create(content: dict[str, int]) -> dict[str, int]:
async def create(shipment: Shipment) -> dict[str, Any]:
    for s in shipments.values():
        content = s["content"]
        weight = s["weight"]
    new_id = max(shipments.keys()) + 1
    if weight < 0:
        raise HTTPException(status_code=400, detail="Weight must be a positive number.")
    elif weight > 50:  # Example weight limit
        raise HTTPException(status_code=406, detail="Weight exceeds the maximum limit.")
    shipments[new_id] = {"content": content, "weight": weight, "status": "placed"}
    return {"id": new_id, "content": content, "weight": weight}


@router.post("/create_ship")
async def create2(shipment: Shipment) -> dict[str, Any]:
    new_id = max(shipments.keys()) + 1
    shipments[new_id] = {
        "content": shipment.content,
        "weight": shipment.weight,
        "status": "placed",
    }
    return {"id": new_id, "content": shipment.content, "weight": shipment.weight}


@router.get("/both/{field}")
def get_shipment_field(field: str, id: int) -> Any:
    return shipments[id][field]


@router.put("/put")
def update(id: int, content: str, weight: float, status: str) -> dict[str, Any]:
    if id not in shipments:
        raise HTTPException(status_code=404, detail="Given id doesn't exist!")
    shipments[id] = {"content": content, "weight": weight, "status": status}
    return {"id": id, "content": content, "weight": weight, "status": status}


@router.patch("/patch")
def patch_shipment(
    # required
    id: int,
    # not required
    content: str | None = None,
    weight: float | None = None,
    status: str | None = None,
):
    shipment = shipments[id]

    # Update the provided fields
    # if content:
    #     shipment["content"] = content
    # if weight:
    #     shipment["weight"] = weight
    # if status:
    #     shipment["status"] = status

    shipment.update(
        {
            "content": content if content is not None else shipment["content"],
            "weight": weight if weight is not None else shipment["weight"],
            "status": status if status is not None else shipment["status"],
        }
    )

    # Reflect changes in datastore
    shipments[id] = shipment
    return shipment


@router.patch("/patch2")
# def patch_shipment_with_req_body(id: int, body: dict[str, Any]) -> dict[str, Any]:
def patch_shipment_with_req_body(
    id: int, body: dict[str, ShipmentStatus]
) -> dict[str, Any]:
    # Update data with given fields
    shipments[id].update(body)
    return shipments[id]


@router.delete("/shipment")
def delete_shipment(id: int) -> dict[str, str]:
    # Remove from datastore
    shipments.pop(id)

    return {"detail": f"Shipment with id #{id} is deleted!"}
