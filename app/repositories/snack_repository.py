"""Direct MongoDB access for the snacks collection"""

from typing import List, Optional

from bson import ObjectId
from pymongo.client_session import ClientSession

from app.infrastructure.mongo_client import get_database
from app.models.snack import Snack

COLLECTION_NAME = "snacks"


def _to_snack(doc: dict) -> Snack:
    doc["_id"] = str(doc["_id"])
    return Snack(**doc)


def get_by_id(snack_id: str) -> Optional[Snack]:
    doc = get_database()[COLLECTION_NAME].find_one({"_id": ObjectId(snack_id)})
    return _to_snack(doc) if doc else None


def list_all() -> List[Snack]:
    cursor = get_database()[COLLECTION_NAME].find()
    return [_to_snack(doc) for doc in cursor]


def list_low_stock(threshold: int) -> List[Snack]:
    cursor = get_database()[COLLECTION_NAME].find({"quantity": {"$lte": threshold}})
    return [_to_snack(doc) for doc in cursor]


def insert(snack: Snack) -> Snack:
    doc = snack.model_dump(by_alias=True, exclude={"id"})
    result = get_database()[COLLECTION_NAME].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _to_snack(doc)


def try_decrement_stock(snack_id: str, session: ClientSession) -> bool:
    """Decrements quantity by 1 only if quantity > 0.
    Returns False if out of stock or if this request lost a race
    against another purchase for the last item."""
    db = get_database()[COLLECTION_NAME]

    result = db.update_one(
        {"_id": ObjectId(snack_id), "quantity": {"$gt": 0}},
        {"$inc": {"quantity": -1}},
        session=session,
    )
    if result.modified_count == 0:
        return False

    db.update_one(
        {"_id": ObjectId(snack_id), "quantity": 0},
        {"$set": {"sold_out": True}},
        session=session,
    )
    return True


def restock(snack_id: str, quantity: int) -> Optional[Snack]:
    get_database()[COLLECTION_NAME].update_one(
        {"_id": ObjectId(snack_id)},
        {"$inc": {"quantity": quantity}, "$set": {"sold_out": False}},
    )
    return get_by_id(snack_id)
