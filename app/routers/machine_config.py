"""Machine configuration router — handles reading and updating admin system limits like low stock thresholds."""

import logging
from fastapi import APIRouter, Depends
from app.services import machine_config_serviceg
from app.core.security import require_api_key
from app.schemas.machine_config.machine_config_response import ThresholdResponse, ThresholdUpdateResponse
from app.schemas.machine_config.machine_config_request import ThresholdUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["machine-config"], dependencies=[Depends(require_api_key)])


@router.get("/settings/low-stock-threshold", response_model=ThresholdResponse)
def get_current_threshold() -> dict:
    """Retrieves the current system count limit that triggers low stock warnings."""
    logger.info("Fetching the current low stock threshold alert setting.")

    value = machine_config_serviceg.get_low_stock_threshold()

    logger.info("Low stock threshold alert setting retrieved successfully.")
    return {"low_stock_threshold": value}


@router.put("/settings/low-stock-threshold", response_model=ThresholdUpdateResponse)
def update_threshold(request: ThresholdUpdateRequest) -> dict:
    """Updates the minimum product count limit that triggers low stock warnings.
    
    The new value must be zero or greater to be accepted by the system.
    """
    logger.info("Processing request to update the low stock threshold alert limit.")
    
    machine_config_serviceg.update_low_stock_threshold(request)

    logger.info("Low stock threshold alert limit updated successfully.")
    return {"status": "success", "updated_threshold": request.low_stock_threshold}
