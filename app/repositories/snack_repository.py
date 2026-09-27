"""Direct MongoDB access for the snacks collection."""

import logging
from typing import List, Optional

from bson import ObjectId
from pymongo.client_session import ClientSession

from app.infrastructure.mongo_client import get_database
from app.models.snack import Snack

logger = logging.getLogger(__name__)

COLLECTION_NAME = "snacks"


def _to_snack(doc: dict) -> Snack:
    """Converts a database dictionary document into a typed Snack model instance."""
    doc["_id"] = str(doc["_id"])
    return Snack(**doc) 


def get_by_name(name: str) -> Optional[Snack]:
    """Finds a single snack record by name using a case-insensitive match."""
    logger.debug("Reading snack record by name: %s", name)
    doc = get_database()[COLLECTION_NAME].find_one(
        {"name": {"$regex": f"^{name}$", "$options": "i"}}
    )
    return _to_snack(doc) if doc else None


def get_by_id(snack_id: str) -> Optional[Snack]:
    """Finds a single snack record by its unique database ID string."""
    logger.debug("Reading snack record by ID: %s", snack_id)
    doc = get_database()[COLLECTION_NAME].find_one({"_id": ObjectId(snack_id)})
    return _to_snack(doc) if doc else None


def list_all() -> List[Snack]:
    """Retrieves all snack documents in the collection without filtering or limits."""
    logger.debug("Listing all snack documents in the collection.")
    cursor = get_database()[COLLECTION_NAME].find()
    return [_to_snack(doc) for doc in cursor]


def list_low_stock(
    threshold: int, name: Optional[str] = None, limit: Optional[int] = None, offset: int = 0
) -> List[Snack]:
    """Retrieves a sorted, paginated list of snacks running below a configured limit threshold."""
    logger.debug("Querying low stock snack list against threshold baseline limit: %d", threshold)
    query_filter: dict = {"quantity": {"$lte": threshold}}
    if name:
        query_filter["name"] = {"$regex": name, "$options": "i"}

    cursor = get_database()[COLLECTION_NAME].find(query_filter).sort("name", 1)
    if limit is not None:
        cursor = cursor.skip(offset).limit(limit)
    return [_to_snack(doc) for doc in cursor]


def count_low_stock(threshold: int, name: Optional[str] = None) -> int:
    """Counts the total number of snack records running below a configured limit threshold."""
    logger.debug("Counting total low stock snack documents against threshold baseline limit: %d", threshold)
    query_filter: dict = {"quantity": {"$lte": threshold}}
    if name:
        query_filter["name"] = {"$regex": name, "$options": "i"}
    return get_database()[COLLECTION_NAME].count_documents(query_filter)


def insert(snack: Snack) -> Snack:
    """Inserts a brand new snack record into the database collection."""
    logger.debug("Inserting a new snack document into database.")
    doc = snack.model_dump(by_alias=True, exclude={"id"})
    result = get_database()[COLLECTION_NAME].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _to_snack(doc)


def try_decrement_stock(snack_id: str, requested_quantity: int, session: ClientSession) -> bool:
    """Deducts units from stock within a session transaction only if enough quantity exists.
    
    Acts as a concurrency check. Automatically updates the 'sold_out' state flag 
    if stock hits exactly zero. Returns False if out of stock or out-raced by another request.
    """
    logger.debug("Attempting atomic stock deduction update for snack ID: %s", snack_id)
    db = get_database()[COLLECTION_NAME]

    result = db.update_one(
        {"_id": ObjectId(snack_id), "quantity": {"$gte": requested_quantity}},
        {"$inc": {"quantity": -requested_quantity}},
        session=session,
    )
    if result.modified_count == 0:
        logger.debug("Stock deduction update rejected due to insufficient quantity or stale state.")
        return False

    db.update_one(
        {"_id": ObjectId(snack_id), "quantity": 0},
        {"$set": {"sold_out": True}},
        session=session,
    )
    return True


def restock(snack_id: str, quantity: int) -> Optional[Snack]:
    """Increments stock counts and clears the sold-out flag for a specific snack item."""
    logger.debug("Applying stock increment restock changes to snack ID: %s", snack_id)
    get_database()[COLLECTION_NAME].update_one(
        {"_id": ObjectId(snack_id)},
        {"$inc": {"quantity": quantity}, "$set": {"sold_out": False}},
    )
    return get_by_id(snack_id)
