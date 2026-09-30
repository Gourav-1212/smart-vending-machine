"""Service layer for daily inventory snapshots — processing and serving reports."""

import logging
from datetime import date, datetime, timezone
from typing import List, Optional

from app.core.exceptions import InvalidQuantityError, NotFoundError
from app.models.inventory_snapshot import InventorySnapshot, SnackSnapshotItem
from app.repositories import snack_repository, cash_float_repository,inventory_snapshot_repository
from app.schemas.snapshots import (
    DailyInventorySnapshotRangeResponse,
    DailyInventorySnapshotResponse,
    SnackSnapshotItemResponse,
)

logger = logging.getLogger(__name__)


def _to_response(snapshot: InventorySnapshot) -> DailyInventorySnapshotResponse:
    """Helper to convert database model to response schema."""
    return DailyInventorySnapshotResponse(
        id=snapshot.id,
        snapshot_date=snapshot.snapshot_date,
        timestamp=snapshot.timestamp,
        total_items=snapshot.total_items,
        total_inventory_value=snapshot.total_inventory_value,
        total_cash=snapshot.total_cash,
        unique_products_count=snapshot.unique_products_count,
        low_stock_count=snapshot.low_stock_count,
        low_stock_items=snapshot.low_stock_items,
        out_of_stock_count=snapshot.out_of_stock_count,
        out_of_stock_items=snapshot.out_of_stock_items,
        snacks=[
            SnackSnapshotItemResponse(
                snack_id=item.snack_id,
                name=item.name,
                quantity=item.quantity,
                price=item.price,
                sold_out=item.sold_out,
            )
            for item in snapshot.snacks
        ],
        denominations=snapshot.denominations,
    )


def get_snapshots_by_range(start: date, end: date) -> DailyInventorySnapshotRangeResponse:
    """Serves a date range inventory history from pre-aggregated snapshots"""
    if start > end:
        raise InvalidQuantityError(
            "Invalid date range",
            reason=f"Start date ({start}) cannot be after end date ({end})"
        )

    logger.info("Serving snapshot inventory report from %s to %s", start, end)
    snapshots = inventory_snapshot_repository.get_range(start.isoformat(), end.isoformat())
   
    return DailyInventorySnapshotRangeResponse(
        start=start.isoformat(),
        end=end.isoformat(),
        days_recorded=len(snapshots),
        snapshots=[_to_response(s) for s in snapshots],
    )


def get_snapshot_by_date(snapshot_date: date) -> DailyInventorySnapshotResponse:
    """Retrieves a single pre-aggregated daily inventory and cash status snapshot."""
    logger.info("Fetching inventory snapshot for date: %s", snapshot_date)
    snapshot = inventory_snapshot_repository.get_by_date(snapshot_date.isoformat())
    if snapshot is None:
        raise NotFoundError(
            "Snapshot not found",
            reason=f"No inventory snapshot exists for date {snapshot_date.isoformat()} — run Airflow DAG to generate it"
        )
    return _to_response(snapshot)


def compute_and_save_daily_snapshot(target_date_str: str, low_stock_threshold: int = 3) -> InventorySnapshot:
    """Compiles machine physical states (snacks, quantities, cash) and idempotently writes to MongoDB.
   
    This is executed by the scheduled Airflow DAG. Key properties:
    1. Idempotent: Running multiple times for the same date updates the same record.
    2. Real-time capture: Records exact current vault and physical machine layouts.
    """
    logger.info("Starting machine snapshot compilation for date: %s", target_date_str)
    
    all_snacks = snack_repository.list_all()
    
    snacks_list: List[SnackSnapshotItem] = []
    low_stock_items: List[str] = []
    out_of_stock_items: List[str] = []
    
    total_items = 0
    total_value = 0

    for snack in all_snacks:
        is_sold_out = snack.quantity <= 0 or getattr(snack, "sold_out", False)
        
        snacks_list.append(
            SnackSnapshotItem(
                snack_id=str(snack.id),
                name=snack.name,
                quantity=snack.quantity,
                price=snack.price,
                sold_out=is_sold_out
            )
        )
        
        total_items += snack.quantity
        total_value += (snack.quantity * snack.price)
        
        if is_sold_out:
            out_of_stock_items.append(snack.name)
        elif snack.quantity <= low_stock_threshold:
            low_stock_items.append(snack.name)

    denominations = {}
    total_cash = 0
    
    
    vault = cash_float_repository.get()

    if vault:
        denominations = vault.denominations
        total_cash = vault.total_cash  
    else:
        denominations = {}
        total_cash = 0

    snapshot = InventorySnapshot(
        snapshot_date=target_date_str,
        timestamp=datetime.now(timezone.utc),
        total_items=total_items,
        total_inventory_value=total_value,
        total_cash=total_cash,
        unique_products_count=len(all_snacks),
        low_stock_count=len(low_stock_items),
        low_stock_items=low_stock_items,
        out_of_stock_count=len(out_of_stock_items),
        out_of_stock_items=out_of_stock_items,
        snacks=snacks_list,
        denominations=denominations,
    )

    saved_snapshot = inventory_snapshot_repository.upsert_snapshot(snapshot)
    logger.info(
        "Successfully produced snapshot for %s: %d total items, $%d cash float across %d unique products.",
        target_date_str,
        total_items,
        total_cash,
        len(all_snacks),
    )
    return saved_snapshot
