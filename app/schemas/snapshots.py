"""Schemas for the scheduled Airflow daily inventory and cash snapshot reporting endpoints."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SnackSnapshotItemResponse(BaseModel):
    """Stock figures for a specific snack on that snapshot day."""
    snack_id: str
    name: str
    quantity: int
    price: int
    sold_out: bool


class DailyInventorySnapshotResponse(BaseModel):
    """Full inventory and cash status document for a single date."""
    id: Optional[str] = Field(default=None, serialization_alias="id")
    snapshot_date: str = Field(..., description="Snapshot calendar date (YYYY-MM-DD)")
    timestamp: datetime
    total_items: int
    total_inventory_value: int
    total_cash: int
    unique_products_count: int
    low_stock_count: int
    low_stock_items: List[str]
    out_of_stock_count: int
    out_of_stock_items: List[str]
    snacks: List[SnackSnapshotItemResponse]
    denominations: Dict[str, int]

    model_config = {"populate_by_name": True}


class DailyInventorySnapshotRangeResponse(BaseModel):
    """Aggregated inventory report over a date range serving from pre-aggregated snapshots."""
    start: str = Field(..., description="Start date (inclusive, YYYY-MM-DD)")
    end: str = Field(..., description="End date (inclusive, YYYY-MM-DD)")
    days_recorded: int
    snapshots: List[DailyInventorySnapshotResponse]
