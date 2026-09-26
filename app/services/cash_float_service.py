"""Cash float service — handles reading and restocking the coins and notes inside the machine."""

import logging
from typing import Dict

from app.core.exceptions import InvalidQuantityError
from app.repositories import cash_float_repository
from app.core.config import get_settings

logger = logging.getLogger(__name__)

def get_denominations() -> Dict[int, int]:
    """Retrieves the current breakdown of all coin and note amounts inside the machine.
    
    Returns an empty dictionary if no cash records exist in the system yet.
    """
    logger.debug("Retrieving current cash float configuration from database.")
    cash_float = cash_float_repository.get()
    if cash_float is None:
        logger.warning("No active cash float records found in the system.")
        return {}
    return cash_float.denominations


def refill_cash(added_denominations: Dict[int, int]) -> Dict[int, int]:
    """Validates and updates the machine's cash vault with newly added coins and notes.
    
    Verifies that each currency type is accepted and that quantities are positive.
    Initializes a new vault record if it is the machine's first-time setup.
    """
    logger.info("Initializing validation check for incoming cash refill request.")
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
        logger.info("First-time setup detected. Initializing fresh cash float records.")
        cash_float_repository.initialize(added_denominations)
    else:
        logger.info("Updating existing inventory balances with refilled amounts.")
        cash_float_repository.update_cash_inventory(added_denominations)
        
    logger.info("Cash float successfully restocked and balanced.")
    updated_cash_float = cash_float_repository.get()
    return updated_cash_float.denominations
