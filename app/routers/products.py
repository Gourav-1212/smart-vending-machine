"""Products router — handles GET /products, GET /status/{id}, and
GET /denominations. Delegates everything to product_service."""

from typing import Dict, List

from fastapi import APIRouter

from app.models.snack import Snack
from app.services import product_service,cash_float_service

router = APIRouter()


@router.get("/products", response_model=List[Snack], tags=["products"])
def get_products() -> List[Snack]:
    return product_service.list_products()


@router.get("/status/{snack_id}", response_model=Snack, tags=["products"])
def get_status(snack_id: str) -> Snack:
    return product_service.get_product_status(snack_id)


@router.get("/denominations", tags=["products"])
def get_denominations() -> Dict[int, int]:
    return cash_float_service.get_denominations()
