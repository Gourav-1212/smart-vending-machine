"""Direct MongoDB access for the cash_float document.
Denomination keys are stored as strings since MongoDB requires
string keys, and converted back to int when read."""

import logging
from typing import Dict, Optional

from pymongo.client_session import ClientSession

from app.infrastructure.mongo_client import get_database
from app.models.cash_float import CashFloat

logger = logging.getLogger(__name__)

COLLECTION_NAME = "cash_float"
SINGLETON_ID = "singleton"


def _to_int_keys(d: dict) -> Dict[int, int]:
    """Converts dictionary keys to integers."""
    return {int(k): v for k, v in d.items()}


def _to_str_keys(d: dict) -> Dict[str, int]:
    """Converts dictionary keys to strings for MongoDB compatibility."""
    return {str(k): v for k, v in d.items()}


def _to_cash_float(doc: dict) -> CashFloat:
    """Converts a database dictionary document into a typed CashFloat model instance.
    
    Transforms MongoDB string keys back into standard integer denominations.
    """
    doc["_id"] = str(doc["_id"])
    doc["denominations"] = _to_int_keys(doc.get("denominations",{}))
    return CashFloat(**doc)


def get() -> Optional[CashFloat]:
    """Retrieves the machine's single cash float configuration document from the database."""
    logger.debug("Reading cash float singleton document from database.")
    doc = get_database()[COLLECTION_NAME].find_one({"_id": SINGLETON_ID})
    return _to_cash_float(doc) if doc else None


def initialize(denominations: Dict[int, int]) -> CashFloat:
    """Creates the initial cash float document with starting currency quantities."""
    logger.debug("Initializing fresh cash float document in database.")
    doc = {
        "_id": SINGLETON_ID,           
        "denominations": _to_str_keys(denominations),
    }
    
    get_database()[COLLECTION_NAME].insert_one(doc)
    return get()


def update_cash_inventory(inventory_changes: Dict[int, int], session: Optional[ClientSession] = None) -> None:
    """Increments or decrements cash denomination totals inside an active session database transaction."""
    logger.debug("Applying inventory modifications to cash float document.")
    mongodb_update_fields = {
        f"denominations.{k}": v for k, v in inventory_changes.items()
    }
    get_database()[COLLECTION_NAME].update_one(
        {"_id": SINGLETON_ID}, 
        {"$inc": mongodb_update_fields}, 
        session=session
    )


