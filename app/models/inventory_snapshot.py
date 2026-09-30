"""InventorySnapshot model — periodic inventory and cash float snapshot taken by Airflow"""


from datetime import datetime, timezone
from typing import Dict, List, Optional


from pydantic import BaseModel, Field




class SnackSnapshotItem(BaseModel):
    snack_id: str
    name: str
    quantity: int
    price: int
    sold_out: bool = False




class InventorySnapshot(BaseModel):
    id: Optional[str] = Field(default=None, validation_alias="_id")
    snapshot_date: str = Field(description="Date formatted as YYYY-MM-DD for daily deduplication")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_items: int
    total_inventory_value: int
    total_cash: int
    unique_products_count: int
    low_stock_count: int = 0
    low_stock_items: List[str] = Field(default_factory=list)
    out_of_stock_count: int = 0
    out_of_stock_items: List[str] = Field(default_factory=list)
    snacks: List[SnackSnapshotItem] = Field(default_factory=list)
    denominations: Dict[str, int] = Field(default_factory=dict)


    model_config = {"populate_by_name": True}