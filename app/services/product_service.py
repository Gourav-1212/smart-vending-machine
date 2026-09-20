"""Product service — read-only logic behind the customer-facing
product/status/denominations endpoints."""

from typing import Dict, List

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.models.snack import Snack
from app.repositories import cash_float_repository, snack_repository


def list_products() -> List[Snack]:
    return snack_repository.list_all()


def get_product_status(snack_id: str) -> Snack:
    snack = snack_repository.get_by_id(snack_id)
    if snack is None:
        raise NotFoundError("Snack not found", reason="No snack with that id")
    return snack


def get_denominations() -> Dict[int, int]:
    cash_float = cash_float_repository.get()
    if cash_float is None:
        return {}
    return cash_float.denominations
