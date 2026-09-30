"""Direct MongoDB access for the inventory_snapshots collection."""

import logging
from typing import List, Optional

from app.infrastructure.mongo_client import get_database
from app.models.inventory_snapshot import InventorySnapshot

logger = logging.getLogger(__name__)


COLLECTION_NAME = "inventory_snapshots"


def _to_model(doc: dict) -> InventorySnapshot:
    """Converts a database dictionary document into a typed InventorySnapshot model."""
    doc["_id"] = str(doc["_id"])
    return InventorySnapshot(**doc)


def upsert_snapshot(snapshot: InventorySnapshot) -> InventorySnapshot:
    """Idempotently saves or updates a daily snapshot document keyed on snapshot_date.
   
    Guarantees running the Airflow DAG twice for the same date leaves one snapshot, not two.
    """
    logger.debug("Upserting daily inventory snapshot for date: %s", snapshot.snapshot_date)
    doc = snapshot.model_dump( exclude={"id"})
   
    get_database()[COLLECTION_NAME].update_one(
        {"snapshot_date": snapshot.snapshot_date}, 
        {"$set": doc},
        upsert=True,
    )
    result_doc = get_database()[COLLECTION_NAME].find_one({"snapshot_date": snapshot.snapshot_date})
    return _to_model(result_doc)


def get_by_date(snapshot_date: str) -> Optional[InventorySnapshot]:
    """Retrieves a single pre-aggregated snapshot record for a specific date."""
    logger.debug("Fetching daily inventory snapshot for date: %s", snapshot_date)
    doc = get_database()[COLLECTION_NAME].find_one({"snapshot_date": snapshot_date})
    return _to_model(doc) if doc else None


def get_range(start_date: str, end_date: str) -> List[InventorySnapshot]:
    """Retrieves pre-aggregated snapshots between start_date and end_date (inclusive), sorted chronologically."""
    logger.debug("Fetching daily inventory snapshots between %s and %s", start_date, end_date)
    cursor = (
        get_database()[COLLECTION_NAME]
        .find({"snapshot_date": {"$gte": start_date, "$lte": end_date}})
        .sort("snapshot_date", 1) 
    )
    return [_to_model(doc) for doc in cursor]
