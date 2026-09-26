# app/schemas/purchase.py
from pydantic import BaseModel, Field

class PurchaseRequest(BaseModel):
    snack_id: str
    cash_amount: int
    quantity: int = Field(default=1, ge=1, description="Number of units to purchase (minimum 1)")


class PurchaseResponse(BaseModel):
    snack_id: str
    snack_name: str
    quantity: int
    unit_price: int
    total_cost: int
    cash_received: int
    change_given: dict
