"""Purchase router — handles POST /purchase, delegates everything to
purchase_service."""

from pydantic import BaseModel
from fastapi import APIRouter

from app.services import purchase_service

router = APIRouter()


class PurchaseRequest(BaseModel):
    snack_id: str
    cash_amount: int


class PurchaseResponse(BaseModel):
    snack_id: str
    snack_name: str
    price_paid: int
    cash_received: int
    change_given: dict


@router.post("/purchase", response_model=PurchaseResponse, tags=["purchase"])
def make_purchase(request: PurchaseRequest) -> PurchaseResponse:
    sale = purchase_service.purchase(request.snack_id, request.cash_amount)
    return PurchaseResponse(
        snack_id=sale.snack_id,
        snack_name=sale.snack_name_at_sale,
        price_paid=sale.unit_price_at_sale,
        cash_received=sale.cash_received,
        change_given=sale.change_given,
    )
