"""Direct MongoDB access for the system_settings collection configuration keys."""

import logging
from typing import Optional
from app.infrastructure.mongo_client import get_database
from app.models.machine_config import SystemSetting

logger = logging.getLogger(__name__)

COLLECTION_NAME = "system_settings"


def get_by_key(key: str) -> Optional[SystemSetting]:
    """Retrieves a specific configuration setting from the database using its unique lookup key."""
    logger.debug("Reading system setting for key: %s from database.", key)
    doc = get_database()[COLLECTION_NAME].find_one({"key": key})
    if doc:
        return SystemSetting(key=doc["key"], threshold=int(doc["threshold"]))
    return None


def upsert_setting(key: str, threshold: int) -> None:
    """Updates an existing configuration rule, or creates a new one if the key does not exist."""
    logger.debug("Upserting system setting value for key: %s in database.", key)
    get_database()[COLLECTION_NAME].update_one(
        {"key": key},
        {"$set": {"threshold": threshold}},
        upsert=True
    )
