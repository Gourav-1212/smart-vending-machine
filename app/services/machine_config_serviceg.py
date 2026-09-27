"""Settings service — handles reading and updating the machine's configuration rules."""

import logging
from app.core.config import get_settings
from app.repositories import machine_config_repository
from app.schemas.machine_config.machine_config_request import ThresholdUpdateRequest

logger = logging.getLogger(__name__)

LOW_STOCK_KEY = "low_stock_config"


def get_low_stock_threshold() -> int:
    """Retrieves the minimum count limit that triggers low stock warnings.
    
    Checks the database first for a custom override, otherwise falls back to 
    the system environment default.
    """
    logger.debug("Checking database for custom low stock threshold setting.")
    setting = machine_config_repository.get_by_key(LOW_STOCK_KEY)
    
    if setting:
        logger.debug("Using custom low stock threshold found in database.")
        return setting.threshold
        
    logger.debug("No custom threshold in database. Using default environment configuration instead.")
    return get_settings().low_stock_threshold


def update_low_stock_threshold(request: ThresholdUpdateRequest) -> None:
    """Saves the new admin threshold rule directly to the repository."""
    if request.low_stock_threshold == 0:
        logger.warning("Low stock threshold updated to 0. Alerts are now disabled.")
        
    logger.info("Saving new low stock threshold setting to database.")
    machine_config_repository.upsert_setting(LOW_STOCK_KEY, request.low_stock_threshold)
    logger.info("Low stock threshold updated successfully.")
