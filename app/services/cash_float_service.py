"""Cash float service — reading and topping up the machine's cash float."""

from typing import Dict

from app.core.exceptions import InvalidQuantityError
from app.repositories import cash_float_repository
from app.core.config import get_settings

def get_denominations() -> Dict[int, int]:
    cash_float = cash_float_repository.get()
    if cash_float is None:
        return {}
    return cash_float.denominations


def refill_cash(added_denominations: Dict[int, int]) -> Dict[int, int]:
    settings = get_settings()
    allowed_denominations = set(settings.denominations)

    for denomination, count in added_denominations.items():
        if denomination not in allowed_denominations:
            raise InvalidQuantityError(
                "Invalid denomination",
                reason=f"{denomination} is not a denomination this machine accepts",
            )

        if count <= 0:
            raise InvalidQuantityError(
                "Invalid quantity",
                reason=f"Refill count for denomination {denomination} must be greater than 0",
            )

    cash_float = cash_float_repository.get()
    if cash_float is None:
        cash_float_repository.initialize(added_denominations)
    else:
        cash_float_repository.update_cash_inventory(added_denominations)

    updated_cash_float = cash_float_repository.get()
    return updated_cash_float.denominations
