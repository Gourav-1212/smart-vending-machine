"""Cash router — handles operations for checking and refilling the machine's cash vault float."""

import logging
from typing import Dict
from fastapi import APIRouter, Depends
from app.services import cash_float_service
from app.core.security import require_api_key
from app.schemas.denomination.denomination_request import RefillRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["cash"], dependencies=[Depends(require_api_key)])


@router.patch("/cash/refill")
def refill_cash(request: RefillRequest) -> Dict[int, int]:
    """Adds specific coin or note counts to the vending machine's cash float.

    Validates that the denominations are accepted by the system before 
    updating the quantities.
    """
    logger.info("Processing request to refill the cash float vault.")

    result = cash_float_service.refill_cash(request.denominations)
    
    logger.info("Cash float vault refilled successfully.")
    return result


@router.get("/denominations")
def get_denominations() -> Dict[int, int]:
    """Retrieves the current quantities of all coin and note denominations inside the machine."""
    logger.info("Retrieving the current cash float inventory levels.")

    result = cash_float_service.get_denominations()

    logger.info("Cash float inventory levels retrieved successfully.")
    return result
