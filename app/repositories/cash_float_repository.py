"""Direct MongoDB access for the cash_float document.
Denomination keys are stored as strings since MongoDB requires
string keys, and converted back to int when read."""

from typing import Dict, Optional

from pymongo.client_session import ClientSession

from app.infrastructure.mongo_client import get_database
from app.models.cash_float import CashFloat

COLLECTION_NAME = "cash_float"
SINGLETON_ID = "singleton"


def _to_cash_float(doc: dict) -> CashFloat:
    doc["_id"] = str(doc["_id"])
    raw_denominations = doc["denominations"]
    clean_denominations = {}
    for key, value in raw_denominations.items():
        numeric_key = int(key)
        clean_denominations[numeric_key] = value
    doc["denominations"] = clean_denominations
    return CashFloat(**doc)



def get() -> Optional[CashFloat]:
    doc = get_database()[COLLECTION_NAME].find_one({"_id": SINGLETON_ID})
    return _to_cash_float(doc) if doc else None


def initialize(denominations: Dict[int, int]) -> CashFloat:
    string_denominations = {}
    for key, value in denominations.items():
        string_key = str(key)
        string_denominations[string_key] = value
    doc = {
        "_id": SINGLETON_ID,           
        "denominations": string_denominations
    }
    
    get_database()[COLLECTION_NAME].insert_one(doc)
    return get()



def update_cash_inventory(inventory_changes: Dict[int, int], session: Optional[ClientSession] = None) -> None:
    mongodb_update_fields = {}
    for cash_value, quantity_changed in inventory_changes.items():
        target_field_path = f"denominations.{cash_value}"
        mongodb_update_fields[target_field_path] = quantity_changed
    get_database()[COLLECTION_NAME].update_one(
        {"_id": SINGLETON_ID}, 
        {"$inc": mongodb_update_fields}, 
        session=session
    )

