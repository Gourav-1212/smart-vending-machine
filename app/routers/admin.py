"""Admin router — all operator routes, each protected by the API key."""

from typing import Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import require_api_key
from app.models.snack import Snack
from app.services import cash_float_service, product_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_api_key)])


class AddSnackRequest(BaseModel):
    name: str
    description: str
    price: int
    quantity: int


class RestockRequest(BaseModel):
    quantity: int


class RefillRequest(BaseModel):
    denominations: Dict[int, int]


@router.post("/snacks", response_model=Snack)
def add_snack(request: AddSnackRequest) -> Snack:
    return product_service.add_product(
        request.name, request.description, request.price, request.quantity
    )


@router.post("/snacks/{snack_id}/restock", response_model=Snack)
def restock_snack(snack_id: str, request: RestockRequest) -> Snack:
    return product_service.restock_product(snack_id, request.quantity)


@router.post("/cash/refill")
def refill_cash(request: RefillRequest) -> Dict[int, int]:
    return cash_float_service.refill_cash(request.denominations)


@router.get("/low-stock", response_model=List[Snack])
def get_low_stock() -> List[Snack]:
    return product_service.get_low_stock_products()
